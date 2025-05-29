var jsPsychDotTask = (function (jspsych) {
    'use strict';
  
      const info = {
          name: "dot-task",
          parameters: {
              /** dot positions */
              dot_positions: {
                  type: jspsych.ParameterType.Int,
                  pretty_name: "Dot positions",
                  default: null,
              },
              /** dot positions */
              stimulus: {
                  type: jspsych.ParameterType.Int,
                  pretty_name: "stim",
                  default: null,
              },
              default_scale: {
                  type: jspsych.ParameterType.Int,
                  pretty_name: "default scale for dot positions",
                  default: null,
              },
              n_to_animate: {
                  type: jspsych.ParameterType.Int,
                  pretty_name: "n to animate",
                  default: null,
              },
              default_shift: {
                  type: jspsych.ParameterType.Int,
                  pretty_name: "shift x/y",
                  default: null,
              },
              default_width: {
                  type: jspsych.ParameterType.Int,
                  pretty_name: "default width of rect",
                  default: null,
              },
              default_height: {
                  type: jspsych.ParameterType.Int,
                  pretty_name: "defualt height of rect",
                  default: null,
              },
          },
      };
      /**
       * dot-task
       * jsPsych plugin for displaying a stimulus and getting a button response
       * @author Josh de Leeuw
       * @see {@link https://www.jspsych.org/plugins/jspsych-dot-task/ dot-task plugin documentation on jspsych.org}
       */
      class DotTaskPlugin {
          constructor(jsPsych) {
              this.jsPsych = jsPsych;
          }
          trial(display_element, trial) {
              //success_audio.src = 'static/sounds/frog_new_sound.mp3'
              
              var success_audio = new Audio()
              success_audio.src = 'static/sounds/success_sound.mp3'
              var fail_audio = new Audio()
              var guess_audio = new Audio()
              guess_audio.src = 'static/sounds/guess_sound.mp3'
              fail_audio.src = 'static/sounds/fail_sound.mp3'
              
              var n_to_animate = trial.n_to_animate
              var screen_fill = 0.95
              var before_jump_time = 800
              var before_allow_next_time = 1000
              var id;
              var default_dot_rad = 8 * 8
              var default_feedback_dot_rad = 80//75
              var default_poss_region_rad = 324 
              var default_poss_region_inner_rad = 30
              var animate_interval_time = 2000
              var animate_over = false;
              
              const scaleSpeed = 0.04; // Rate of scale increase
              var init_scale = 0.7
              const angleSpeed = 0//2*Math.PI/(((1-init_scale)/scaleSpeed)-0.5)
              
              var images = [];
  
              var rcanvas = ""
              var rctx = ""
              var canvas = ""
              var ctx = ""
  
              // Array to hold the image URLs
              var imageUrls = [
                'static/imgs/pond.png',
                'static/imgs/pad.png',
                'static/imgs/frog.png',
                'static/imgs/ripple.png',
                'static/imgs/star.png',
                'static/imgs/outline.png'
              ];
              var imagesLoaded = 0;
              function handleImageLoad() {
                imagesLoaded++;
                // Check if all images have finished loading
                if (imagesLoaded === imageUrls.length) {
                    init_html()
                    animate()
                }
              }
              function LoadImages() {
                  for (var i = 0; i < imageUrls.length; i++) {
                      var image = new Image();
                      image.src = imageUrls[i];
                      image.onload = handleImageLoad;
                      images.push(image);
                  }
              }
              LoadImages()
  
  
  
              function get_max_canvas_dims() {
                  return([window.innerWidth * screen_fill, window.innerHeight * screen_fill])
              }
  
              //scale all default values by this number
              //calculated based on current screen w/h
              function get_scale_from_default() {
                  var [max_canvas_w, max_canvas_h] = get_max_canvas_dims()
                  return(Math.min(max_canvas_w/trial.default_width, max_canvas_h/trial.default_height))
              }
  
              //get dot positions according to true positions, default scale, and scale from default
              function get_display_dot_positions() {
                  var xs = []
                  var ys = []
                  var shift_x = trial.default_shift[0]
                  var shift_y = trial.default_shift[1]
                  var scale = trial.default_scale * get_scale_from_default()
                  for (var i = 0; i < trial.dot_positions[0].length; i++) {
                      xs.push((trial.dot_positions[0][i] + shift_x) * scale)
                      ys.push((trial.dot_positions[1][i] + shift_y) * scale)
                  }
                  return [xs,ys]
              }
              function prevent(e) {
                  e.preventDefault();
              }
              function on_click_prevent_default(e) {
                  prevent(e)
                  on_click(canvas, e)
              }
              //dimensions of current screen, based on default dimensions and scale given this persons screen size
              function get_canvas_dims() {
                  var sfd = get_scale_from_default()
                  return([sfd * trial.default_width, sfd * trial.default_height])
              }
              
  
              function add_listeners(canvas) {
                  //add click listener
                  display_element
                  .querySelector("#jspsych-canvas-game-exit")
                  .addEventListener("click", () => {
                      if (animate_over) {
                          end_trial()
                      } else {
                          clearInterval(id);
                          setTimeout(() => {
                              end_trial()
                          }, animate_interval_time+100);
                      }
                  });
                  //maybe put these in update html and update next?
                  window.addEventListener("resize", update_html);
                  window.addEventListener("orientationchange", update_html);
                  canvas.addEventListener('mousedown', function(e) {
                      on_click(canvas, e)
                  })
                  window.addEventListener('touchmove', function(e) {
                      e.preventDefault();
                  }, {passive:false});
                  canvas.addEventListener('touchstart', function(e) {
                      e.preventDefault();
                      on_click(canvas, e)
                  }, false)
              }
  
  
              function init_html() {
                  var [curr_w, curr_h] = get_canvas_dims()
                  var border_w = 1
                  var html =
                  '<div style="position:absolute; left:10px;"><button id="jspsych-canvas-game-exit" class="jspsych-btn"' +
                  ">" +
                  "exit" +
                  "</button></div>";
                  
                  html += '<div class="canvas-container" style="width:' + curr_w + 'px; height:' + curr_h + 'px;">' +
                          '<canvas id="rotatingCanvas" width="' + (curr_w) + '" height="' + (curr_h) + '"></canvas>' +
                          '<canvas id="staticCanvas" width="' + curr_w + '" height="' + curr_h + '" style="border:' + border_w + 'px solid black;"></canvas>' +
                          '</div>'
                  
                  display_element.innerHTML = html
                  //make canvas non-selectable
                  canvas = document.getElementById('staticCanvas')
                  ctx = canvas.getContext("2d");
                  rcanvas = document.getElementById('rotatingCanvas');
                  rctx = rcanvas.getContext('2d');
  
                  add_listeners(canvas)
                  canvas.style.userSelect = 'none';
                  canvas.style.webkitTouchCallout = 'none';
                  canvas.style.webkitUserSelect = 'none';
                  canvas.style.khtmlUserSelect = 'none';
                  canvas.style.mozUserSelect = 'none';
                  canvas.style.msUserSelect = 'none';
                  canvas.style.webkitTapHighlightColor = 'transparent';
                  canvas.style.webkitTapHighlightColor = 'rgba(0,0,0,0)';
  
                  draw_bg(ctx, curr_w, curr_h)
              }   
  
  
              function draw_star(ctx, x, y, rad, o)
              {
                  ctx.drawImage(images[4],  x-(rad/2), y-(rad/2), rad, rad);
              }
  
  
              function add_dot(x, y, rad, curr_angle, curr_scale) {
                  // Clear the canvas
                  rctx.clearRect(0, 0, rotatingCanvas.width, rotatingCanvas.height);
                  // Save the current canvas state
                  rctx.save();
                  // Translate the canvas to the center of the canvas
                  rctx.translate(x, y);
                  //Rotate the canvas by the angle (in radians)
                  rctx.rotate(curr_angle);
                  rctx.translate(-x, -y);
                  // Draw the image at its center
                  var temp_rad = rad*curr_scale
                  rctx.drawImage(images[4],  x-(temp_rad/2), y-(temp_rad/2), temp_rad, temp_rad);
                  // Restore the canvas state
                  rctx.restore();
                  // Update the angle for rotation
                  curr_angle += angleSpeed;
                  // Increase the scale
                  curr_scale += scaleSpeed;
                  // Request animation frame to create a smooth animation loop
                  if (curr_scale < 1) {
                      requestAnimationFrame(function() {
                          add_dot(x,y,rad, curr_angle, curr_scale);
                      });
                  }
              }
              
              var arrow_speed = 0.08
              function animateArrow(progress, start, end, guess, c) {
                  // Clear the canvas
                  //ctx.clearRect(0, 0, canvas.width, canvas.height);
                  var [curr_w, curr_h] = get_canvas_dims()
                  var [dot_positions, scale] = get_display_dot_positions()
                  for(var i=0;i<=dot_idx;i++) {
                      var o = (i+3)/(dot_idx+3)
                      //draw_circle(ctx, dot_positions[0][i], dot_positions[1][i], dot_rad * curr_w, dot_color, o)
                      draw_arrow([dot_positions[0][i-1], dot_positions[1][i-1]], [dot_positions[0][i], dot_positions[1][i]], 1, ctx, 1) 
                  }
  
                  //draw guess
                  //draw_circle(ctx, guess[0], guess[1], success_rad*curr_w, c, 0.4)
                  //draw_circle_outline(ctx, guess[0], guess[1], dot_rad*curr_w, "black", 1)
                  //draw arrow
                  draw_arrow(start, end, progress, ctx, 1.5) 
  
                  // Request the next animation frame
                  if (progress < 1) {
                      requestAnimationFrame(animateArrow.bind(null, progress + arrow_speed, start, end, guess, c));
                  } else {
                      //draw_circle(ctx, dot_positions[0][dot_idx+1], dot_positions[1][dot_idx+1], dot_rad*curr_w*1.5, "black", 1)
                  }
              }
              function draw_arrow(start, end, progress, ctx, sub) {
                  if (progress>1) {
                      progress =1
                  }
                  var sfd = get_scale_from_default()
                  var dot_rad = sfd * default_dot_rad
                  // Calculate current arrow position based on progress (0 to 1)
                  var curr_w = get_canvas_dims()[0]
                  var currX = start[0] + (end[0] - start[0]) * progress;
                  var currY = start[1] + (end[1] - start[1]) * progress;
  
                  var vec = [currX-start[0], currY-start[1]]
                  var mag = Math.sqrt((vec[0]*vec[0]) + (vec[1]*vec[1]))
                  if (mag>0) {
                      var norm_vec = [vec[0]/mag, vec[1]/mag]
                      var sc = dot_rad*curr_w*sub
                      var [currX, currY] = [currX - (norm_vec[0]*sc), currY - (norm_vec[1]*sc)]
                  }
                  // Calculate arrow direction
                  const dx = currX - start[0];
                  const dy = currY - start[1];
                  const angle = Math.atan2(dy, dx);
                  // Draw the arrow line
                  ctx.beginPath();
                  ctx.moveTo(start[0], start[1]);
                  ctx.lineTo(currX, currY);
                  ctx.stroke();
                  // Draw the arrowhead
                  const arrowSize = 5;
                  ctx.save(); // Save the current context state
                  ctx.translate(currX, currY);
                  ctx.rotate(angle);
                  ctx.beginPath();
                  ctx.moveTo(0, 0);
                  ctx.lineTo(-arrowSize, arrowSize / 2);
                  ctx.lineTo(-arrowSize, -arrowSize / 2);
                  ctx.closePath();
                  ctx.globalAlpha = 0.7;
                  ctx.fillStyle = "black";
                  ctx.fill();
                  ctx.restore();
              }
       
  
              //draw pad at click pos
              function update_html_with_guess(x,y) {
                  var sfd = get_scale_from_default()
                  var dot_rad = sfd * default_dot_rad
                  draw_outline(ctx, x, y, dot_rad*1.2, 1)
              }   
  
              //show lily's new pos and splash or lily pad
              function update_html_with_feedback(x,y, success) {
                  //get dot positions according to true positions, default scale, and scale from default
                  var dot_positions = get_display_dot_positions()
                  var sfd = get_scale_from_default()
                  //draw true next
                  add_dot(dot_positions[0][dot_idx+1], dot_positions[1][dot_idx+1], default_dot_rad * sfd, 0, init_scale);
              } 
  
              //static html at curr point
              function update_html() {
                  //remove last spinny star
                  rctx.clearRect(0, 0, rcanvas.width, rcanvas.height);
                  ctx.clearRect(0, 0, rcanvas.width, rcanvas.height);
                  //get dot positions according to true positions, default scale, and scale from default
                  var dot_positions = get_display_dot_positions()
                  var sfd = get_scale_from_default()
                  //draw all prev dots
                  for(i=0;i<=dot_idx;i++) {
                      //now make color relative to idx
                      var o = (i+3)/(dot_idx+3)
                      if (i==dot_idx) {
                          draw_star(ctx, dot_positions[0][i], dot_positions[1][i], default_dot_rad * sfd, o)
                      } else {
                          draw_star(ctx, dot_positions[0][i], dot_positions[1][i], default_dot_rad * sfd,o)
                      }
                  }
              } 
  
              //add 1 dot
              function update_html_animate() {
                  //get dot positions according to true positions, default scale, and scale from default
                  var dot_positions = get_display_dot_positions()
                  var sfd = get_scale_from_default()
                  animateArrow(0, [dot_positions[0][dot_idx], dot_positions[1][dot_idx]], [dot_positions[0][dot_idx+1], dot_positions[1][dot_idx+1]], [0,0], "black");
                  add_dot(dot_positions[0][dot_idx+1], dot_positions[1][dot_idx+1], default_dot_rad * sfd, 0, init_scale);
              }  
                      
              function animate() {
                  var n_animated = 0
                  id = setInterval(animate_next, animate_interval_time);
                  function animate_next() {
                    if (n_animated==n_to_animate) {
                      clearInterval(id);
                      animate_over = true;
                      guess_audio.play();
                      ignore_click=false;
                      start_time = performance.now();
                    } else {
                      animate_func()
                      n_animated = n_animated + 1
                    }
                  }
              }
  
              function animate_func() {
                  console.log(dot_idx)
                  //current scale from default sizes
                  var sfd = get_scale_from_default()
                  var scale = trial.default_scale * sfd
                  scale_at_click[dot_idx] = scale
                  //check success
                  setTimeout(() => {
                      fail_audio.play();
                      setTimeout(() => {
                          update_html_animate()
                          dot_idx = dot_idx + 1
                          setTimeout(() => {
                              update_html()
                          }, 1200);
                      }, 200);
                  }, 100);
              }
  
  
              function draw_bg(ctx, w, h)
              {
                  //ctx.drawImage(images[0], 0, 0, w, h);
              }
              
              function draw_outline(ctx, x, y, rad, o)
              {
                  ctx.drawImage(images[5],  x-(rad/2), y-(rad/2), rad, rad);
              }
  
              function draw_star(ctx, x, y, rad, o)
              {
                  ctx.globalAlpha = o;
                  ctx.drawImage(images[4],  x-(rad/2), y-(rad/2), rad, rad);
                  ctx.globalAlpha = 1;
              }
              function draw_pad(ctx, x, y, rad, o)
              {
                  ctx.drawImage(images[1],  x-(rad/2), y-(rad/2), rad, rad);
              }
              function draw_splash(ctx, x, y, rad, o)
              {
                  ctx.globalAlpha = o;
                  ctx.drawImage(images[3],  x-(rad/2), y-(rad/2), rad, rad);
                  ctx.globalAlpha = 1;
              }
  
              // initialize stuff
              var start_time = performance.now();
              var scale_at_click = []
              var click_x = [];
              var click_y = [];
              var guess_success = [];
              var dot_idx = -1;
              var rts = []
              for (var i = 0; i < trial.dot_positions[0].length; i++) {
                  click_x.push(null)
                  click_y.push(null)
                  scale_at_click.push(null)
                  guess_success.push(null)
                  rts.push(null)
              }
  
              var end_time = null;
              var ignore_click = true;
  
  
              function get_click_pos(canvas, click_event) {
                  const rect = canvas.getBoundingClientRect()
                  //var x = click_event.touches[0].clientX - rect.left - 1
                  //var y = click_event.touches[0].clientY - rect.top - 1
                  var x = click_event.clientX - rect.left - 1
                  var y = click_event.clientY - rect.top - 1
                  return [x,y]
              }
              
              //deal w user input
              function on_click(canvas, e) {
                  if(ignore_click) {
                      return;
                  }
                  var [x,y] = get_click_pos(canvas, e)
                  click_func(x,y)
              }
              function click_func(x,y) {
                  if(ignore_click) {
                      return;
                  }
                  //current dot positions
                  var dot_positions = get_display_dot_positions()
                  //current scale from default sizes
                  var sfd = get_scale_from_default()
                  if (check_valid(x, y, dot_positions, sfd)) {
                      ignore_click=true;
                      //record rt
                      end_time = performance.now();
                      rts[dot_idx] = end_time - start_time;
  
                      //record click, scaled down in terms of true x/y coords
                      var scale = trial.default_scale * sfd
                      var shift_x = trial.default_shift[0]
                      var shift_y = trial.default_shift[1]
                      click_x[dot_idx] = (x/scale)-shift_x
                      click_y[dot_idx] = (y/scale)-shift_y
                      scale_at_click[dot_idx] = scale
                      
                      //check success
                      var success = check_success(x, y, dot_positions, sfd)
                      guess_success[dot_idx] = success
  
                      //update html with feedback / next dot
                      display_feedback(success, x, y)
                  }
              }
  
              function check_success(x,y, dot_positions, sfd) {
                  var feedback_dot_rad = default_feedback_dot_rad * sfd
                  var true_x = dot_positions[0][dot_idx+1]
                  var true_y = dot_positions[1][dot_idx+1]
                  return (Math.hypot(x - true_x, y - true_y) < feedback_dot_rad)
              }
              function check_valid(x, y, dot_positions, sfd) {
                  var poss_region_rad = sfd * default_poss_region_rad
                  var poss_region_inner_rad = sfd * default_poss_region_inner_rad
  
                  var prev_x = dot_positions[0][dot_idx]
                  var prev_y = dot_positions[1][dot_idx]
                  var d = Math.hypot(x - prev_x, y - prev_y)
                  return (d > poss_region_inner_rad)
                  return ((d < poss_region_rad) && (d > poss_region_inner_rad))
              }
  
  
              function display_feedback(success, x, y) {
                  //show pad at click pos
                  update_html_with_guess(x,y)
                  if (success) {
                      success_audio.play();
                  } else {
                      setTimeout(() => {
                          fail_audio.play();
                      }, 100);
                  }
                  setTimeout(() => {
                      //show next true
                      update_html_with_guess(x,y)
                      update_html_with_feedback(x,y, success)
                      dot_idx = dot_idx + 1
                      setTimeout(() => {
                          if (dot_idx == trial.dot_positions[0].length-1) {
                              end_trial()
                          } else {
                              //redraw
                              update_html()
                              ignore_click=false;
                              start_time = performance.now();
                          };
                      }, before_allow_next_time+200);
                  }, before_jump_time);
              };
  
   
              // function to end trial when it is time
              const end_trial = () => {
                  // kill any remaining setTimeout handlers
                  this.jsPsych.pluginAPI.clearAllTimeouts();
                  // gather the data to store for the trial
                  var trial_data = {
                      rt: rts,
                      response_x: click_x,
                      response_y: click_y,
                      response_success: guess_success,
                      scale_at_response: scale_at_click
                  };
                  window.removeEventListener('touchmove', function(e) {
                      e.preventDefault();
                  }, {passive:false});
                  // clear the display
                  display_element.innerHTML = "";
                  window.removeEventListener("resize", update_html);
                  window.removeEventListener("orientationchange", update_html);
                  // move on to the next trial
                  this.jsPsych.finishTrial(trial_data);
              };
          }
      }
      DotTaskPlugin.info = info;
  
      return DotTaskPlugin;
  
  })(jsPsychModule);
  