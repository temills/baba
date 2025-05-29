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
      },
      rule_points: {
        type: null,
        pretty_name: "rule_points",
        default: 5
      },
      win_points: {
        type: null,
        pretty_name: "win_points",
        default: 10
      },
      display_points: {
        type: null,
        pretty_name: "win_points",
        default: true
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

    // we need time before start, grid, steps, times of steps, won, obj_history, won, loss_reason
    var actions = []
    var action_times = []

    //variables
    var allow_keydown;
    var last_key_up = true
    var allow_restart = false
    var game_active = false;
    const rules = trial.rules;
    const time_limit = trial.time_limit;
    const obj_types = trial.obj_types;
    const obj_probs = trial.obj_probs;
    const game_cols = trial.grid_cols
    const game_rows = trial.grid_rows + 1 + 9
    const grid_rows = trial.grid_rows;
    const grid_cols = game_cols + time_limit*5;
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
    var trial_start_time;
    var game_start_time;
    var game_end_time;
    //setup html
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
        game_start_time = Date.now() - trial_start_time;
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
        //if (gamestate.time % 2 == 0) {
            //grid_steps = grid_steps + 1
            //step_grid()
        //}
        if (gamestate.time >= time_limit) {
            game_active = false
            end_game(false, "Time's up")
        }
    }

    function step_grid() {
        grid_steps = grid_steps + 1
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
            game_active = false
            end_game(false, "Out of bounds")
        }
    }

    function setup_game() {
        trial_start_time = Date.now()
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
        if (game_active && allow_keydown && last_key_up) {
            allow_keydown = false
            last_key_up = false
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
                case " ":
                    event.preventDefault()
                    player_movement(0, 0)
                    break;
                default:
                    allow_keydown = true
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
        //allow_keydown = true
        last_key_up = true
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

    var rule_violated = -1
    function rule_violation(seq) {
        //return true if violation
        for (var i=0; i < rules.length; i++) {
            if (!rules[i](seq)) {
                rule_violated = i
                return(true)
            }
        }
        return(false)
    }

    function player_movement(dx, dy) {
        actions.push([dx,dy])
        action_times.push(Date.now()-trial_start_time)


        var nx = gamestate.xpos + dx;
        var ny = gamestate.ypos + dy;
        //if movement in bounds
        if (nx >= 0 && nx < game_cols && ny >= 0 && ny < game_rows) {
            gamestate.xpos = nx;
            gamestate.ypos = ny;
            update_canvas()
            //update sequence
            if (avatar_in_grid() && (dx!=0 || dy!=0)) {
                var obj = avatar_on_obj()
                gamestate.seq.push(obj)
                console.log(gamestate.seq)
                if (rule_violation(gamestate.seq)) {
                    game_active = false
                    end_game(false, "Rule violation:")
                }
            }
            if (avatar_in_endzone()) {
                game_active = false
                end_game(true)
            }
        }
        if (game_active) {
            setTimeout(() => {
                step_grid()
                allow_keydown = true
              }, 250);
            //step_grid()
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
    var termination_condition = -1;
    function end_game(won, reason=null) {
        clearInterval(timer);
        game_end_time = Date.now()-trial_start_time;
        game_active = false;
        ctx.globalAlpha = 0.8;
        ctx.fillStyle = "white";
        ctx.fillRect(0, 0, game_cols*sqr_size, game_rows*sqr_size);
        ctx.globalAlpha = 1;
        if (won) {
            termination_condition = "Won"
            game_status = "won"
            draw_text("You win!", 50, "green", (grid_start+grid_rows+1.5))
            if (trial.display_points) {
                draw_text("+ " + trial.win_points + " points", 20, "green", (grid_start+grid_rows+2.5))
                draw_text('Press space to continue', 20, "green", (grid_start+grid_rows+3.2));
            } else {
                draw_text('Press space to continue', 20, "green", (grid_start+grid_rows+2.5));
            }
        } else {
            game_status = "lost"
            termination_condition = reason
            if (rule_violated>=0) {
                var y = grid_start+grid_rows+0.75
                draw_text(reason, 20, "red", (y));
                y+=0.6
                draw_text(trial.rule_text[rule_violated], 18, "red", y)
                y+=1.35
                draw_text("You lose!", 50, "red", y)
                y+=0.8
                if (trial.display_points) {
                    draw_text('- ' + trial.rule_points + ' points', 20, "red", y);
                    y+=0.8
                }
                draw_text('Press space to continue', 20, "red", y);
            } else {
                var y = grid_start+grid_rows+0.75
                draw_text(reason, 20, "red", (y));
                y+=1.35
                draw_text("You lose!", 50, "red", y)
                y+=0.9
                draw_text('Press space to continue', 20, "red", y);
            }
        }
        setTimeout(() => {
            allow_restart = true
          }, 1500);
    }





    // Call external functions
    //createVisuals(display_element);
    //handleMovement();

    const endTrial = (won) => {
      var trial_data = {won:won,
                        seq:gamestate.seq,
                        game_time:gamestate.time,
                        grid:grid,
                        actions:actions,
                        action_times:action_times,
                        termination_condition:termination_condition,
                        rule_violated:rule_violated,
                        game_start_time:game_start_time,
                        game_end_time:game_end_time,
                        timelimit:time_limit,
                        rules:rules_str
                        };
      console.log(trial_data)
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