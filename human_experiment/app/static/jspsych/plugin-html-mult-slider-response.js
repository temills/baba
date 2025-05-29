var jsPsychHtmlMultSliderResponse = (function (jspsych) {
    'use strict';

    const info = {
        name: "html-mult-slider-response",
        parameters: {
            /** The HTML string to be displayed */
            stimulus: {
                type: jspsych.ParameterType.HTML_STRING,
                pretty_name: "Stimulus",
                default: undefined,
            },
            /** Sets the minimum value of the slider. */
            min: {
                type: jspsych.ParameterType.INT,
                pretty_name: "Min slider",
                default: 0,
            },
            /** Sets the maximum value of the slider */
            max: {
                type: jspsych.ParameterType.INT,
                pretty_name: "Max slider",
                default: 100,
            },
            /** Sets the starting value of the slider */
            slider_start: {
                type: jspsych.ParameterType.INT,
                pretty_name: "Slider starting value",
                default: 50,
            },
            /** Sets the step of the slider */
            step: {
                type: jspsych.ParameterType.INT,
                pretty_name: "Step",
                default: 1,
            },
            /** Array containing the labels for the slider. Labels will be displayed at equidistant locations along the slider. */
            labels: {
                type: jspsych.ParameterType.HTML_STRING,
                pretty_name: "Labels",
                default: [],
                array: true,
            },
            /** Width of the slider in pixels. */
            slider_width: {
                type: jspsych.ParameterType.INT,
                pretty_name: "Slider width",
                default: null,
            },
            /** Label of the button to advance. */
            button_label: {
                type: jspsych.ParameterType.STRING,
                pretty_name: "Button label",
                default: "Continue",
                array: false,
            },
            /** If true, the participant will have to move the slider before continuing. */
            require_movement: {
                type: jspsych.ParameterType.BOOL,
                pretty_name: "Require movement",
                default: true,
            },
            /** Any content here will be displayed below the slider. */
            prompts: {
                type: jspsych.ParameterType.HTML_STRING,
                pretty_name: "Prompt",
                default: [],
            },
            /** How long to show the stimulus. */
            stimulus_duration: {
                type: jspsych.ParameterType.INT,
                pretty_name: "Stimulus duration",
                default: null,
            },
            /** How long to show the trial. */
            trial_duration: {
                type: jspsych.ParameterType.INT,
                pretty_name: "Trial duration",
                default: null,
            },
            /** If true, trial will end when user makes a response. */
            response_ends_trial: {
                type: jspsych.ParameterType.BOOL,
                pretty_name: "Response ends trial",
                default: true,
            },
        },
    };
    /**
     * **html-mult-slider-response**
     *
     * jsPsych plugin for showing an HTML stimulus and collecting a slider response
     *
     * @author Josh de Leeuw
     * @see {@link https://www.jspsych.org/plugins/jspsych-html-mult-slider-response/ html-mult-slider-response plugin documentation on jspsych.org}
     */
    class HtmlSliderResponsePlugin {
        constructor(jsPsych) {
            this.jsPsych = jsPsych;
        }
        trial(display_element, trial) {
            // half of the thumb width value from jspsych.css, used to adjust the label positions
            var half_thumb_width = 7.5;
            var html = '<div id="jspsych-html-mult-slider-response-wrapper" style="margin: 100px 0px;">';
            //add stimulus
            html += '<div id="jspsych-html-mult-slider-response-stimulus">' + trial.stimulus + "</div><br>";

            //add slider for each prompt
            for (var i=0;i<trial.prompts.length; i++) {
                //add prompts
                html += trial.prompts[i];
                //add slider
                html += '<div class="jspsych-html-mult-slider-response-container" style="position:relative; margin: 0 auto 3em auto; ';
                if (trial.slider_width !== null) {
                    html += "width:" + trial.slider_width + "px;";
                }
                else {
                    html += "width:auto;";
                }
                html += '">';
                html +=
                    '<input type="range" class="jspsych-slider" value="' +
                        trial.slider_start +
                        '" min="' +
                        trial.min +
                        '" max="' +
                        trial.max +
                        '" step="' +
                        trial.step +
                        '" id="jspsych-html-mult-slider-response-' + i + '-response"></input>';
                html += "<div>";
                //add labels
                for (var j = 0; j < trial.labels.length; j++) {
                    var label_width_perc = 100 / (trial.labels.length - 1);
                    var percent_of_range = j * (100 / (trial.labels.length - 1));
                    var percent_dist_from_center = ((percent_of_range - 50) / 50) * 100;
                    var offset = (percent_dist_from_center * half_thumb_width) / 100;
                    html +=
                        '<div style="border: 1px solid transparent; display: inline-block; position: absolute; ' +
                            "left:calc(" +
                            percent_of_range +
                            "% - (" +
                            label_width_perc +
                            "% / 2) - " +
                            offset +
                            "px); text-align: center; width: " +
                            label_width_perc +
                            '%;">';
                    html += '<span style="text-align: center; font-size: 80%;">' + trial.labels[j] + "</span>";
                    html += "</div>";
                }
                html += "</div>";
                html += "</div>";

            }


            // add submit button
            html +=
                '<button id="jspsych-html-mult-slider-response-next" class="jspsych-btn" ' +
                    (trial.require_movement ? "disabled" : "") +
                    ">" +
                    trial.button_label +
                    "</button>";
            display_element.innerHTML = html;
            var response = {
                rts: [],
                responses: null,
            };
            var sliders_moved = Array(trial.prompts.length).fill(0);
            if (trial.require_movement) {
                const enable_button = () => {
                    //enable button if all sliders have been moved
                    var sum=0
                    for (var i=0; i<sliders_moved.length;i++) {
                        sum = sum + sliders_moved[i]
                    }
                    if (sum == sliders_moved.length) {
                        display_element.querySelector("#jspsych-html-mult-slider-response-next").disabled = false;
                    }
                };
                var get_f = (k) => {
                    return (() => {
                        sliders_moved[k]=1
                        var t = performance.now();
                        if (response.rts.length < k+1) {
                            response.rts.push(undefined)
                            response.rts[k] = t;
                        }
                        enable_button()
                    })
                }
                for(var i=0;i<trial.prompts.length;i++) {
                    display_element
                    .querySelector("#jspsych-html-mult-slider-response-" + i + "-response")
                    .addEventListener("mousedown", get_f(i));
                    display_element
                        .querySelector("#jspsych-html-mult-slider-response-" + i + "-response")
                        .addEventListener("touchstart", get_f(i));
                    display_element
                        .querySelector("#jspsych-html-mult-slider-response-" + i + "-response")
                        .addEventListener("change", get_f(i));
                }
            }
            const end_trial = () => {
                this.jsPsych.pluginAPI.clearAllTimeouts();
                // save data
                var trialdata = {
                    rts: response.rts,
                    stimulus: trial.stimulus,
                    prompts: trial.prompts,
                    slider_start: trial.slider_start,
                    responses: response.responses,
                };
                display_element.innerHTML = "";
                // next trial
                this.jsPsych.finishTrial(trialdata);
            };
            display_element
                .querySelector("#jspsych-html-mult-slider-response-next")
                .addEventListener("click", () => {
                    // measure response time
                    var t = performance.now();
                    response.rts.push(t);
                    response.responses = []
                    for(var i=0;i<trial.prompts.length;i++) {
                        response.responses.push(display_element.querySelector("#jspsych-html-mult-slider-response-" + i + "-response").valueAsNumber)
                    }
                    if (trial.response_ends_trial) {
                        end_trial();
                    }
                    else {
                        display_element.querySelector("#jspsych-html-mult-slider-response-next").disabled = true;
                    }
            });
            if (trial.stimulus_duration !== null) {
                this.jsPsych.pluginAPI.setTimeout(() => {
                    display_element.querySelector("#jspsych-html-mult-slider-response-stimulus").style.visibility = "hidden";
                }, trial.stimulus_duration);
            }
            // end trial if trial_duration is set
            if (trial.trial_duration !== null) {
                this.jsPsych.pluginAPI.setTimeout(end_trial, trial.trial_duration);
            }
            var startTime = performance.now();
        }
    } 
    HtmlSliderResponsePlugin.info = info;
    return HtmlSliderResponsePlugin;
})(jsPsychModule);
