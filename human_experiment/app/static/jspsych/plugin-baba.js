// Define the plugin info
const info = {
    name: "baba",
    parameters: {
        game_type: {
            type: null,
            pretty_name: "game_type",
            default: null,
        },
        image_urls: {
            type: null,
            pretty_name: "image_urls",
            default: null,
        },
        title: {
            type:null,
            pretty_name:"title",
            default:null,
        },
        socket: {
            type:null,
            pretty_name:"socket",
            default:null,
        }
    },
};


class jsPsychBaba {
    constructor(jsPsych) {
        this.jsPsych = jsPsych;
    }

    trial(display_element, trial) {

        var grid;
        var grid_width;
        var grid_height;
        var cell_size;
        var actions = []
        var agent_positions = []
        var action_times = []
        var timer;
        var giveup_timeout;
        var trial_start_time;
        var game_end_time;
        var game_type = trial.game_type
        var game_time = 0;
        var won = 0
        var game_active = false
        var game_ended = false
        var allow_keydown = false
        var grids = []
        var last_key_up = true
        var giveup_time = 600000
        var html;
        var ctx;
        var canvas;


        const socket = trial.socket
        socket.removeAllListeners("game_update");

        var idx_to_img_key = {0: 'unseen', 1: 'empty', 2: 'wall', 3: 'floor', 4: 'door', 5: 'key', 6: 'ball', 7: 'box', 9: 'lava', 10: 'agent', 11: 'water', 12: 'flag', 13: 'baba', 16: 'is_word', 19: 'ball_word', 20: 'wall_word', 21: 'door_word', 22: 'key_word', 23: 'baba_word', 24: 'water_word', 25: 'you_word', 26: 'win_word', 27: 'fball', 28: 'fdoor', 29: 'fkey', 30: 'fwall', 31: 'border', 32: 'fwater', 33: 'rock', 34: 'rock_word', 35: 'flag_word', 36: 'keke_word', 37: "keke", 38:"stop_word", 39:"float_word", 40:"sink_word"}
        var image_urls = trial.image_urls
        var image_cache = {};
        var images_loaded = 0;

        load_images();
        
        //keyboard listeners
        document.addEventListener('keydown', handle_keydown);
        document.addEventListener('keyup', handle_keyup);


        // Listen for game state updates
        socket.on("game_update", function (new_state) {
            grid = new_state["grid"]
            agent_positions.push(new_state["agent_pos"])
            grids.push(grid)
            if (!game_active) {
                grid_width = grid.length
                grid_height = grid[0].length
                console.log("setting up game")
                setup_game(grid_width, grid_height)
            } else {
                update_canvas(grid); 
                if (new_state["won"]==1) {
                    won = true
                    end_game()
                } else {
                    allow_keydown = true
                }
            }
        });

        // Send user actions to the server
        function send_action(action) {
            allow_keydown = false
            socket.emit("player_action", { action: action, game_type: game_type});
        }

        // Send user actions to the server
        function init_game(game_type) {
            console.log("Initializing game...")
            socket.emit("init_game", { game_type: game_type});
        }

        
        function on_image_loaded() {
            images_loaded++;
            if (images_loaded === Object.keys(image_urls).length) {
                init_game(game_type);
            }
        }
        function load_images() {
            for (var key in image_urls) {
                var image = new Image();
                image.onload = on_image_loaded;
                image.src = image_urls[key];
                image_cache[key] = image; 
            }
        }

        function restartGame() {
            if (game_active) {
                actions.push(-1)
                action_times.push(Date.now()-trial_start_time)
                init_game(game_type);
            }
        }

        function tick() {
            game_time += 1
            document.getElementById("timer").textContent = "Time: " + game_time;
            //document.getElementById("timer").innerHTML = "Time: " + game_time;
        }

        function setup_game(grid_width, grid_height) {
            cell_size = window.innerHeight * (1/2)/grid_height
            html = `
            <div id="header" style="text-align: center;">
                <h2 id="title">` + trial.title + `</h3>
                <h3 id="timer">Time: ` + 0 + `</h3>
            </div>
            <div style="position: relative; display: flex; justify-content: center;">
                <div style="position: relative;">
                    <canvas id="game-canvas" width="` + (cell_size*grid_width) + `" height="` + (cell_size*grid_height) + `" style=""></canvas>
                </div>
            </div>
            <button id="restartButton"
                    style="
                    margin-top: 30px;
                    padding: 10px 20px;
                    font-size: 20px;
                    background-color: white;
                    color: black;
                    border: 2px solid #333;
                    border-radius: 5px;
                    cursor: pointer;
                    ">
                    Reset</button>
            `;
            
            display_element.innerHTML = html;
            document.getElementById('restartButton').addEventListener('click', function() {
                restartGame();
            });
            canvas = document.getElementById("game-canvas");
            ctx = canvas.getContext('2d')

            update_canvas(grid); 
            game_active = true
            allow_keydown = true
            trial_start_time = Date.now()
            timer = setInterval(tick, 1000);

            giveup_timeout = setTimeout(function() {
                let existingButton = document.getElementById("giveUpButton");
                console.log(existingButton)
                if (!existingButton) {
                    let giveUpButton = document.createElement("button");
                    giveUpButton.id = "giveUpButton";
                    giveUpButton.innerHTML = "Give up";
                    giveUpButton.style = `
                        margin-top: 20px;
                        padding: 10px 20px;
                        font-size: 20px;
                        background-color: #eee;
                        color: black;
                        border: 2px solid #333;
                        border-radius: 5px;
                        cursor: pointer;
                    `;
                
                    giveUpButton.onclick = function() {
                        // Call your give up function here
                        give_up();
                    };
                
                    // Append the button under the reset button
                    document.getElementById("restartButton").parentNode.appendChild(giveUpButton);
                }
            }, giveup_time); 
        }




        function give_up() {
            if (!game_ended) {
                actions.push(-2)
                action_times.push(Date.now()-trial_start_time)
                game_end_time = Date.now()-trial_start_time;
                game_active = false;
                game_ended = true
                endTrial()
            }
        }


        function handle_keydown(event) {
            if (game_active) {
                if (allow_keydown && last_key_up) {
                    allow_keydown = false
                    last_key_up = false
                    switch (event.key) {
                        case "ArrowUp":
                            event.preventDefault()
                            player_movement(1)
                            break;
                        case "ArrowDown":
                            event.preventDefault()
                            player_movement(3)
                            break;
                        case "ArrowLeft":
                            event.preventDefault()
                            player_movement(4)
                            break;
                        case "ArrowRight":
                            event.preventDefault()
                            player_movement(2)
                            break;
                        default:
                            allow_keydown = true
                            break;
                    }
                }
            } else if (game_ended) { 
                if (event.key==" ") {
                    endTrial()
                }
            }
        }

        function handle_keyup(event) {
            last_key_up = true
        }

        function player_movement(action) {
            actions.push(action)
            action_times.push(Date.now()-trial_start_time)
            send_action(action)
        }

        function update_canvas(grid) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = "black"
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            for (var row=0; row < grid_height; row++) {
                for (var col=0; col < grid_width; col++) {
                    var img_key = idx_to_img_key[grid[col][row][0]]
                    var img = image_cache[img_key];
                    var x = cell_size * col
                    var y = cell_size * row
                    if (!(img_key in image_cache)) {
                        console.log("Img not found for key: ", img_key)
                    }
                    ctx.drawImage(img, x, y, cell_size, cell_size);
                }
            }
        }

        function end_game() {
            game_active = false;
            game_ended = true
            clearInterval(timer);
            clearTimeout(giveup_timeout);
            document.getElementById('restartButton').style.display = 'none';
            if (document.getElementById("giveUpButton") != null) {
                document.getElementById("giveUpButton").style.display = 'none';
            }
            game_end_time = Date.now()-trial_start_time;
            ctx.globalAlpha = 0.6;
            ctx.fillStyle = "white";
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.globalAlpha = 1;
            //this should always be true
            if (won) {
                var img = image_cache["congrats"];
                var x = canvas.width/10
                var y = canvas.height/4
                ctx.drawImage(img, x, y, canvas.width*4/5, canvas.height/2);
            }
        }

        const endTrial = () => {
            socket.removeAllListeners("game_update");
            if (document.getElementById("giveUpButton") != null) {
                document.getElementById("giveUpButton").remove();
            }
            clearInterval(timer);
            var trial_data = {won:won,
                              game_type:game_type,
                              actions:actions,
                              agent_pos:agent_positions,
                              action_times:action_times,
                              grids:grids,
                              trial_start_time:trial_start_time,
                              game_end_time:game_end_time};

            document.removeEventListener('keydown', handle_keydown);
            document.removeEventListener('keyup', handle_keyup);
            display_element.innerHTML = "";
            this.jsPsych.finishTrial(trial_data);
        };

    }
}

// Export plugin
jsPsychBaba.info = info;
export default jsPsychBaba;