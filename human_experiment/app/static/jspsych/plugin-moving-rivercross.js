// Import external modules
//import { createVisuals } from './createVisuals.js';
//import { handleMovement } from './handleMovement.js';

// Define the plugin info
const info = {
    name: "river-cross",
    parameters: {
        title: {
            type: null,//jsPsych.ParameterType.INT,
            pretty_name: "",
            default: "",
        },
      game_rows: {
        type: null,//jsPsych.ParameterType.INT,
        pretty_name: "game_rows",
        default: 15,
      },
      game_cols: {
        type: null,
        pretty_name: "game_cols",
        default: 15,
      },
      grid_rows: {
        type: null,
        pretty_name: "grid_rows",
        default: 5,
      },
      time_limit: {
        type: null,
        pretty_name: "time_limit",
        default: 30,
      },
      sqr_size: {
        type: null,
        pretty_name: "sqr_size",
        default: 40,
      },
      rules: {
        type: null,
        pretty_name: "rules",
        default: []
      },
      rule_text: {
        type: null,
        pretty_name: "rule_text",
        default: []
      },
      obj_types: {
        type: null,
        pretty_name: "obj_types",
        default: [1, 2, 3, 4, 5]
      },
      obj_probs: {
        type: null,
        pretty_name: "obj_probs",
        default: [0.2, 0.2, 0.2, 0.2, 0.2]
      }
    },
  };


class jsPsychRiverCross {
  constructor(jsPsych) {
    this.jsPsych = jsPsych;
  }

  trial(display_element, trial) {
    //TODO
    //figure out experiment setup 
    //collect data eventually
    //animate river?

    //variables
    var allow_keydown;
    var allow_restart = false
    var game_active = false;
    const rules = trial.rules;
    const time_limit = trial.time_limit;
    const obj_types = trial.obj_types;
    const obj_probs = trial.obj_probs;
    const game_cols = trial.game_cols
    const game_rows = trial.game_rows
    const grid_rows = trial.grid_rows;
    const grid_cols = game_cols + time_limit;
    var action_history = [];
    var grid;
    const grid_start = 1;
    var grid_steps = 0; //make this separate from time
    var sqr_size = Math.min((window.innerHeight * (3/4))/game_rows, trial.sqr_size)
    //var sqr_size = trial.sqr_size; //could have this adapt to screen size

    const color_map = {
        1: '#ff790f',
        2: 'red',
        3: 'green',
        4: 'blue',
        5: 'purple'
    };
    const bg_color = '#62cb71'
    const avatar_color = "black"
    var timer;

    var gamestate;
    var game_status = null;

    //setup html
    /*const html = `
                <div id="header">
                    <h3 id="timer">Seconds remaining: ` + time_limit + `</h3>
                </div>
                <div id='game-body' class='Flex-Container' style="display: flex; align-items: center">
                    <canvas id="game-canvas" width="` + (sqr_size*game_cols) + `" height="` + (sqr_size*game_rows) + `" style="margin: auto; border:1px solid #000000;"></canvas>
                    <div style="border: 1px solid black; padding: 20px; width: 200px; height: auto;box-sizing: border-box;">"blah"</div>
                </div>
                <br>
                <div>
                    <div class="flex-button" id='start-div'>
                        <button id="start" class="jspsych-btn" style="font-size:28px; border-color:black">Start game</button>
                    </div>
                </div>
                `;*/
    var rule_text = trial.rule_text;
    var rules_str = "<b>Rules:</b>"
    for (var i=0; i<rule_text.length; i++) {
        rules_str += '<br><b>' + (i+1) + '.</b> ' + rule_text[i]
    }

    const html = `
                <div id="header" style="text-align: center;">
                    <h2 id="title">` + trial.title + `</h2>
                    <h3 id="timer">Seconds remaining: ` + time_limit + `</h3>
                </div>
                <div style="position: relative; display: flex; justify-content: center;">
                    <div style="position: relative;">
                        <canvas id="game-canvas" width="` + (sqr_size*game_cols) + `" height="` + (sqr_size*game_rows) + `" style="border:1px solid #000000;"></canvas>
                    </div>
                    <div id="text-box" style="position: absolute; left: calc(100% + 20px); top: 50%; transform: translateY(-50%); padding: 5px; border: 1px solid black; width: 250px; text-align:left; font-size:16px; ; line-height: 1.5;">
                        ` + rules_str + `
                    </div>
                </div>
                <div style="text-align: center; margin-top: 20px;">
                    <button id="start" class="jspsych-btn" style="font-size:28px; border-color:black;">Start game</button>
                </div>
                `;

    display_element.innerHTML = html;
    var canvas = document.getElementById("game-canvas");
    var ctx = canvas.getContext('2d')

    setup_game()

    //add button which starts game
    $("#start").click(start_game);
    //keyboard listeners
    document.addEventListener('keydown', handle_keydown);
    document.addEventListener('keyup', handle_keyup);





    function start_game() {
        $("#start").hide();
        allow_keydown = true;
        //start timer for every second
        timer = setInterval(tick, 1000);
        //also update canvas on player movement
        game_active = true
    }

    function tick() {
        gamestate.time = gamestate.time + 1
        document.getElementById("timer").innerHTML = "Seconds remaining: " + (time_limit-gamestate.time);

        //if avatar in river, move avatar, and lose if we're out of bounds
        if (gamestate.time % 2 == 0) {
            grid_steps = grid_steps + 1
            step_grid()
        }
        if (gamestate.time >= time_limit) {
            end_game(false, "Time's up")
        }
    }

    function step_grid() {
        if (avatar_in_grid()) {
            //if in even row, move to right, if in odd row, move to left
            var row = gamestate.ypos - grid_start
            if (row % 2 == 0) {
                gamestate.xpos = gamestate.xpos + 1
            } else {
                gamestate.xpos = gamestate.xpos - 1
            }
        }
        update_canvas()
        //check out of bounds
        if (!avatar_in_bounds()) {
            end_game(false, "Out of bounds")
        }
    }

    function setup_game() {
        grid = generate_rand_grid(grid_rows, grid_cols, obj_types, obj_probs);
        gamestate = init_gamestate()
        update_canvas();
        document.getElementById("timer").innerHTML = "Seconds remaining: " + (time_limit-gamestate.time);
    }

    function avatar_in_grid() {
        return (grid_start <= gamestate.ypos) && (gamestate.ypos < grid_start+grid_rows)
    }
    function avatar_in_bounds() {
        return (0 <= gamestate.ypos) && (gamestate.ypos < game_rows) && (0 <= gamestate.xpos) && (gamestate.xpos < game_cols)
    }
    function avatar_in_endzone() {
        return (grid_start > gamestate.ypos)
    }

    function handle_keydown(event) {
        if (game_active && allow_keydown) {
            allow_keydown = false
            switch (event.key) {
                case "ArrowUp":
                    event.preventDefault()
                    player_movement(0, -1)
                    break;
                case "ArrowDown":
                    event.preventDefault()
                    player_movement(0, 1)
                    break;
                case "ArrowLeft":
                    event.preventDefault()
                    player_movement(-1, 0)
                    break;
                case "ArrowRight":
                    event.preventDefault()
                    player_movement(1, 0)
                    break;
            }
        } else {
            if (allow_restart) {
                if (event.key == " ") {
                    endTrial(game_status=="won")
                    
                    // allow_restart = false
                    // setup_game()
                    // $("#start").show();
                }
            } 
        }
    }
    function handle_keyup(event) {
        allow_keydown = true
    }

    function avatar_on_obj() {
        var vis_grid = get_visible_grid(grid, grid_steps);
        var obj = vis_grid[gamestate.ypos-grid_start][gamestate.xpos]
        if (obj == undefined) {
            console.log(vis_grid[gamestate.ypos-grid_start])
            console.log(vis_grid[gamestate.ypos-grid_start][gamestate.xpos])
        }
        return obj;
    }

    function rule_violation(seq) {
        //return true if violation
        for (var i=0; i < rules.length; i++) {
            if (!rules[i](seq)) {
                return(true)
            }
        }
        return(false)
    }

    function player_movement(dx, dy) {
        var nx = gamestate.xpos + dx;
        var ny = gamestate.ypos + dy;
        //if movement in bounds
        if (nx >= 0 && nx < game_cols && ny >= 0 && ny < game_rows) {
            gamestate.xpos = nx;
            gamestate.ypos = ny;
            update_canvas()
            //update sequence
            if (avatar_in_grid()) {
                var obj = avatar_on_obj()
                gamestate.seq.push(obj)
                console.log(gamestate.seq)
                if (rule_violation(gamestate.seq)) {
                    end_game(false, "Rule violation")
                }
            }
            if (avatar_in_endzone()) {
                end_game(true)
            }
        }
    }


    function get_visible_grid(grid, step) {
        var vis_grid = [];
        for(var row=0; row<grid.length; row++) {
            var vis_row = grid[row].slice(step, step+game_cols);
            if (row % 2 == 0) {
                vis_row.reverse();
            }
            vis_grid.push(vis_row);
        }
        return(vis_grid);
    }

    function draw_square(color, x, y) {
        ctx.fillStyle = color;
        ctx.fillRect(x*sqr_size, y*sqr_size, sqr_size, sqr_size);
    }
    function draw_bg() {
        ctx.fillStyle = bg_color;
        ctx.fillRect(0, 0, game_cols*sqr_size, grid_start*sqr_size);
        ctx.fillStyle = "#D3D3D3";
        ctx.fillRect(0, grid_start*sqr_size, game_cols*sqr_size, (grid_start+game_rows)*sqr_size);
    }
    function draw_grid() {
        //ctx.fillStyle = "lightblue";
        //ctx.fillRect(0, grid_start*sqr_size, game_cols*sqr_size, grid_rows*sqr_size);
        //draw each square in visible grid
        var vis_grid = get_visible_grid(grid, grid_steps);
        for (var row=0; row < vis_grid.length; row++) {
            for (var col=0; col < vis_grid[row].length; col++) {
                const number = vis_grid[row][col];
                const color = color_map[number];
                const x = col*sqr_size
                const y = (row+grid_start)*sqr_size
                ctx.fillStyle = color;
                var x_buffer = (sqr_size/30)
                var y_buffer = (sqr_size/30)*2
                ctx.fillRect(x+x_buffer, y+y_buffer, sqr_size-(x_buffer*2), sqr_size-(y_buffer*2));
                
                //if (col==0 || col==vis_grid[row].length-1) {
                // ctx.globalAlpha = Math.max(0, ((time_limit/3) - gamestate.time)/(time_limit/3));
                // if (row % 2 == 0) {
                //     draw_arrow(x+(sqr_size/8), y+(sqr_size/2), x+(7*sqr_size/8), y+(sqr_size/2))
                // } else {
                //     draw_arrow(x+(7*sqr_size/8), y+(sqr_size/2), x+(sqr_size/8), y+(sqr_size/2))
                // }
                // ctx.globalAlpha = 1
                //}
            }
        }
    }
    function draw_avatar() {
        if (avatar_in_bounds()) {
            //draw_square(avatar_color, gamestate.xpos, gamestate.ypos)
            var x = gamestate.xpos*sqr_size
            var y = gamestate.ypos*sqr_size
            var buffer;

            if (avatar_in_grid()) {
                buffer = (sqr_size/30)*2
            } else {
                buffer = (sqr_size/30)
            }
            ctx.beginPath();
            ctx.fillStyle = avatar_color;
            //ctx.fillRect(x+x_buffer, y+y_buffer, sqr_size-(x_buffer*2), sqr_size-(y_buffer*2));
            ctx.arc(x+(sqr_size/2), y+(sqr_size/2), (sqr_size/2)-buffer, 0, Math.PI * 2);
            ctx.fill(); // Fill the circle
            ctx.closePath();
        }
    }

    function draw_arrow(fromX, fromY, toX, toY, headLength = 7) {
        const angle = Math.atan2(toY - fromY, toX - fromX);

        // Draw the line
        ctx.beginPath();
        ctx.moveTo(fromX, fromY);
        ctx.lineTo(toX, toY);
        ctx.strokeStyle = "white";
        ctx.lineWidth = 1;
        ctx.stroke();

        // Draw the arrowhead
        ctx.beginPath();
        ctx.moveTo(toX, toY);
        ctx.lineTo(
            toX - headLength * Math.cos(angle - Math.PI / 6),
            toY - headLength * Math.sin(angle - Math.PI / 6)
        );
        ctx.lineTo(
            toX - headLength * Math.cos(angle + Math.PI / 6),
            toY - headLength * Math.sin(angle + Math.PI / 6)
        );
        ctx.lineTo(toX, toY);
        ctx.closePath();
        ctx.fillStyle = "white";
        ctx.fill();
    }

    function update_canvas() {
        //draw background
        ctx.clearRect(0, 0, game_cols*sqr_size, game_rows*sqr_size);
        draw_bg()
        draw_grid()
        draw_avatar()
    }

    /*
    function update_canvas_size() {
        var max_sqr_width = window.innerWidth/game_cols
        var h1 = document.getElementById('header').offsetHeight
        var h2 = document.getElementById('blah').offsetHeight
        var max_sqr_height = (window.innerHeight - document.getElementById('header').offsetHeight - document.getElementById('blah').offsetHeight)/game_rows
        //on window resize, could update sqr_size, update canvas dims, and redraw canvas
        sqr_size = Math.min(max_sqr_width, max_sqr_height)
        canvas.width = (sqr_size*game_cols)
        canvas.height = (sqr_size * game_rows)
    }*/

    // functions
    function init_gamestate() {
        return {
             xpos: Math.floor(game_cols / 2),
             ypos: game_rows-1,
             time: 0,
             seq: []
         }
    }


    //var g = [[3, 1, 4, 2, 2, 2, 3, 5, 3, 2, 5, 2, 5, 3, 2], [4 3 5 2 3 2 2 3 1 4 5 3 4 1 4; 1 3 2 2 5 3 2 1 5 2 2 3 2 2 3; 3 3 2 2 4 5 2 2 2 5 2 4 5 1 2; 3 3 2 5 2 2 2 2 3 3 5 5 5 4 3]
    // function generate_rand_grid(rows, cols, elements, probs) {
    //     const array = [];
    //     function getRandomElement() {
    //         const random = Math.random();
    //         let sum = 0;
    //         for (let i = 0; i < probs.length; i++) {
    //             sum += probs[i];
    //             if (random < sum) {
    //                 return elements[i];
    //             }
    //         }
    //     }
    //     for (let i = 0; i < rows; i++) {
    //         const row = [];
    //         for (let j = 0; j < cols; j++) {
    //             row.push(getRandomElement());
    //         }
    //         array.push(row);
    //     }
    //     return array;
    // }
    function generate_rand_grid_prev(rows, cols, elements, probs) {
        const array = [];
        function getRandomElement() {
            const random = Math.random();
            let sum = 0;
            for (let i = 0; i < probs.length; i++) {
                sum += probs[i];
                if (random < sum) {
                    return elements[i];
                }
            }
        }
        for (let i = 0; i < rows; i++) {
            const row = [];
            for (let j = 0; j < cols; j++) {
                row.push(getRandomElement());
            }
            array.push(row);
        }
        return array;
    }
    function generate_rand_grid(rows, cols, elements, probs) {
        if (elements.length !== probs.length) {
            throw new Error("The number of elements must match the number of probabilities.");
        }
    
        const array = [];
    
        for (let i = 0; i < rows; i++) {
            // Calculate the exact number of each element for this row
            const counts = probs.map(p => Math.round(p * cols));
            const total = counts.reduce((sum, count) => sum + count, 0);
    
            // Adjust counts to match the total number of columns (cols)
            let adjustment = cols - total;
            while (adjustment !== 0) {
                for (let j = 0; j < counts.length; j++) {
                    if (adjustment === 0) break;
                    if (adjustment > 0) {
                        counts[j]++;
                        adjustment--;
                    } else if (counts[j] > 0) {
                        counts[j]--;
                        adjustment++;
                    }
                }
            }
    
            // Create the row by repeating elements based on the counts
            const row = [];
            for (let j = 0; j < elements.length; j++) {
                row.push(...Array(counts[j]).fill(elements[j]));
            }
    
            // Shuffle the row to randomize the order
            for (let k = row.length - 1; k > 0; k--) {
                const randIdx = Math.floor(Math.random() * (k + 1));
                [row[k], row[randIdx]] = [row[randIdx], row[k]];
            }
    
            array.push(row);
        }
    
        return array;
    }
    

    function draw_text(text, size, color, y) {
        ctx.font = size + 'px Open Sans';
        ctx.fillStyle = color; // Text color
        const text_width = ctx.measureText(text).width;
        ctx.fillText(text, (game_cols/2)*sqr_size - (text_width/2), y*sqr_size);
    }

    function end_game(won, reason=null) {
        clearInterval(timer);
        game_active = false;
        ctx.globalAlpha = 0.8;
        ctx.fillStyle = "white";
        ctx.fillRect(0, 0, game_cols*sqr_size, game_rows*sqr_size);
        ctx.globalAlpha = 1;
        if (won) {
            game_status = "won"
            draw_text("You win!", 50, "green", (grid_start+grid_rows+1.5))
            draw_text('Press space to continue', 20, "green", (grid_start+grid_rows+2.5));
        } else {
            game_status = "lost"
            draw_text(reason + ":", 20, "red", (grid_start+grid_rows+0.75));
            draw_text("You lose!", 50, "red", (grid_start+grid_rows+2.1))
            draw_text('Press space to continue', 20, "red", (grid_start+grid_rows+3.0));
        }
        allow_restart = true
    }





    // Call external functions
    //createVisuals(display_element);
    //handleMovement();

    const endTrial = (won) => {
      var trial_data = {won:won,
                        seq:gamestate.seq,
                        game_time:gamestate.time,
                        grid:grid,
                        //keypresses:action_list,,

                        };
      this.jsPsych.finishTrial(trial_data);
      document.removeEventListener('keydown', handle_keydown);
      document.removeEventListener('keyup', handle_keyup);
      display_element.inner_html = "";
    };

  }
}

// Export plugin
jsPsychRiverCross.info = info;
export default jsPsychRiverCross;