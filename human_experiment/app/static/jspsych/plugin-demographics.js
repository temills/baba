var jsPsychDemographics = (function (jspsych) {
    'use strict';
  
    const info = {
        name: "demographics",
        parameters: {
            /** Array containing one or more objects with parameters for the question(s) that should be shown on the page. */
            text_questions: {
                type: jspsych.ParameterType.COMPLEX,
                array: true,
                pretty_name: "Text Questions",
                default: undefined,
                nested: {
                    /** Question prompt. */
                    prompt: {
                        type: jspsych.ParameterType.HTML_STRING,
                        pretty_name: "Prompt",
                        default: undefined,
                    },
                    /** Placeholder text in the response text box. */
                    placeholder: {
                        type: jspsych.ParameterType.STRING,
                        pretty_name: "Placeholder",
                        default: "",
                    },
                    /** The number of rows for the response text box. */
                    rows: {
                        type: jspsych.ParameterType.INT,
                        pretty_name: "Rows",
                        default: 1,
                    },
                    /** The number of columns for the response text box. */
                    columns: {
                        type: jspsych.ParameterType.INT,
                        pretty_name: "Columns",
                        default: 40,
                    },
                    /** Whether or not a response to this question must be given in order to continue. */
                    required: {
                        type: jspsych.ParameterType.BOOL,
                        pretty_name: "Required",
                        default: false,
                    },
                    /** Name of the question in the trial data. If no name is given, the questions are named Q0, Q1, etc. */
                    name: {
                        type: jspsych.ParameterType.STRING,
                        pretty_name: "Question Name",
                        default: "",
                    },
                },
            },
            multi_questions: {
                type: jspsych.ParameterType.COMPLEX,
                array: true,
                pretty_name: "Multi Questions",
                nested: {
                    /** Question prompt. */
                    prompt: {
                        type: jspsych.ParameterType.HTML_STRING,
                        pretty_name: "Prompt",
                        default: undefined,
                    },
                    /** Array of multiple choice options for this question. */
                    options: {
                        type: jspsych.ParameterType.STRING,
                        pretty_name: "Options",
                        array: true,
                        default: undefined,
                    },
                    /** Whether or not a response to this question must be given in order to continue. */
                    required: {
                        type: jspsych.ParameterType.BOOL,
                        pretty_name: "Required",
                        default: false,
                    },
                    /** If true, then the question will be centered and options will be displayed horizontally. */
                    horizontal: {
                        type: jspsych.ParameterType.BOOL,
                        pretty_name: "Horizontal",
                        default: false,
                    },
                    /** Name of the question in the trial data. If no name is given, the questions are named Q0, Q1, etc. */
                    name: {
                        type: jspsych.ParameterType.STRING,
                        pretty_name: "Question Name",
                        default: "",
                    },
                },
            },
            /** If true, the order of the questions in the 'questions' array will be randomized. */
            randomize_question_order: {
                type: jspsych.ParameterType.BOOL,
                pretty_name: "Randomize Question Order",
                default: false,
            },
            /** HTML-formatted string to display at top of the page above all of the questions. */
            preamble: {
                type: jspsych.ParameterType.HTML_STRING,
                pretty_name: "Preamble",
                default: null,
            },
            /** Label of the button to submit responses. */
            button_label: {
                type: jspsych.ParameterType.STRING,
                pretty_name: "Button label",
                default: "Continue",
            },
            /** Setting this to true will enable browser auto-complete or auto-fill for the form. */
            autocomplete: {
                type: jspsych.ParameterType.BOOL,
                pretty_name: "Allow autocomplete",
                default: false,
            },
        },
    };
    /**
     * **demographics**
     *
     * jsPsych plugin for presenting multiple choice survey questions
     *
     * @author Shane Martin
     * @see {@link https://www.jspsych.org/plugins/jspsych-demographics/ demographics plugin documentation on jspsych.org}
     */
    class DemographicsPlugin {
        constructor(jsPsych) {
            this.jsPsych = jsPsych;
        }
        trial(display_element, trial) {
            var plugin_id_name = "jspsych-demographics";
            var html = "";
            // inject CSS for trial
            html += '<style id="jspsych-demographics-css">';
            html +=
                ".jspsych-survey-multi-choice-question { margin-top: 2em; margin-bottom: 2em; text-align: left; }" +
                    ".jspsych-survey-multi-choice-text span.required " +
                    ".jspsych-survey-multi-choice-horizontal .jspsych-survey-multi-choice-text {  text-align: center;}" +
                    ".jspsych-survey-multi-choice-option { line-height: 2; }" +
                    ".jspsych-survey-multi-choice-horizontal .jspsych-survey-multi-choice-option {  display: inline-block;  margin-left: 1em;  margin-right: 1em;  vertical-align: top;}" +
                    "label.jspsych-survey-multi-choice-text input[type='radio'] {margin-right: 1em;}";
            html += "</style>";
            // show preamble text
            // form element
            if (trial.autocomplete) {
                html += '<form id="jspsych-demographics-form">';
            }
            else {
                html += '<form id="jspsych-demographics-form" autocomplete="off">';
            }


            for (var i = 0; i < trial.text_questions.length; i++) {
                if (typeof trial.text_questions[i].rows == "undefined") {
                    trial.text_questions[i].rows = 1;
                }
            }
            for (var i = 0; i < trial.text_questions.length; i++) {
                if (typeof trial.text_questions[i].columns == "undefined") {
                    trial.text_questions[i].columns = 40;
                }
            }
            for (var i = 0; i < trial.text_questions.length; i++) {
                if (typeof trial.text_questions[i].value == "undefined") {
                    trial.text_questions[i].value = "";
                }
            }

            // generate question order
            var text_question_order = [];
            for (var i = 0; i < trial.text_questions.length; i++) {
                text_question_order.push(i);
            }
            // add questions
            for (var i = 0; i < trial.text_questions.length; i++) {
                var question = trial.text_questions[text_question_order[i]];
                var question_index = text_question_order[i];
                html +=
                    '<div id="jspsych-demographics-text-' +
                        question_index +
                        '" class="jspsych-survey-text-question" style="margin: 2em 0em; text-align:left;">';
                html += '<p class="jspsych-survey-text"><b>' + question.prompt + "</b></p>";
                var autofocus = i == 0 ? "autofocus" : "";
                var req = question.required ? "required" : "";
                if (question.rows == 1) {
                    html +=
                        '<input type="text" id="input-' +
                            question_index +
                            '"  name="#jspsych-demographics-text-response-' +
                            question_index +
                            '" data-name="' +
                            question.name +
                            '" size="' +
                            question.columns +
                            '" ' +
                            autofocus +
                            " " +
                            req +
                            ' placeholder="' +
                            question.placeholder +
                            '"></input>';
                }
                else {
                    html +=
                        '<textarea id="input-' +
                            question_index +
                            '" name="#jspsych-demographics-text-response-' +
                            question_index +
                            '" data-name="' +
                            question.name +
                            '" cols="' +
                            question.columns +
                            '" rows="' +
                            question.rows +
                            '" ' +
                            autofocus +
                            " " +
                            req +
                            ' placeholder="' +
                            question.placeholder +
                            '"></textarea>';
                }
                html += "</div>";
            }
            



            // generate question order. this is randomized here as opposed to randomizing the order of trial.questions
            // so that the data are always associated with the same question regardless of order
            var question_order = [];
            for (var i = 0; i < trial.multi_questions.length; i++) {
                question_order.push(i);
            }
            // add multiple-choice questions
            for (var i = 0; i < trial.multi_questions.length; i++) {
                // get question based on question_order
                var question = trial.multi_questions[question_order[i]];
                var question_id = question_order[i];
                // create question container
                var question_classes = ["jspsych-survey-multi-choice-question"];
                if (question.horizontal) {
                    question_classes.push("jspsych-survey-multi-choice-horizontal");
                }
                html +=
                    '<div id="jspsych-demographics-multi-' +
                        question_id +
                        '" class="' +
                        question_classes.join(" ") +
                        '"  data-name="' +
                        question.name +
                        '">';
                // add question text
                html += '<p class="jspsych-survey-multi-choice-text">' + question.prompt;
                if (question.required) {
                    html += "<span class='required'>*</span>";
                }
                html += "</p>";
                // create option radio buttons
                for (var j = 0; j < question.options.length; j++) {
                    // add label and question text
                    var option_id_name = "jspsych-demographics-multi-option-" + question_id + "-" + j;
                    var input_name = "jspsych-demographics-multi-response-" + question_id;
                    var input_id = "jspsych-demographics-multi-response-" + question_id + "-" + j;
                    var required_attr = question.required ? "required" : "";
                    // add radio button container
                    html += '<div id="' + option_id_name + '" class="jspsych-survey-multi-choice-option">';
                    html += '<label class="jspsych-survey-multi-choice-text" for="' + input_id + '">';
                    html +=
                        '<input type="radio" name="' +
                            input_name +
                            '" id="' +
                            input_id +
                            '" value="' +
                            question.options[j] +
                            '" ' +
                            required_attr +
                            "></input>";
                    html += question.options[j] + "</label>";
                    html += "</div>";
                }
                html += "</div>";
            }
            
            //////////////////////////////////////////
            


            // add submit button
            html +=
            '<input type="submit" id="' +
                plugin_id_name +
                '-next" class="' +
                plugin_id_name +
                ' jspsych-btn"' +
                (trial.button_label ? ' value="' + trial.button_label + '"' : "") +
                "></input>";
            html += "</form>";
            // render
            display_element.innerHTML = html;

            // backup in case autofocus doesn't work
            display_element.querySelector("#input-" + text_question_order[0]).focus();

            document.querySelector("form").addEventListener("submit", (event) => {
                event.preventDefault();
                // measure response time
                var endTime = performance.now();
                var response_time = Math.round(endTime - startTime);
                // create object to hold responses
                var multi_question_data = {};
                for (var i = 0; i < trial.multi_questions.length; i++) {
                    var match = display_element.querySelector("#jspsych-demographics-multi-" + i);
                    var id = "Q" + i;
                    var val;
                    if (match.querySelector("input[type=radio]:checked") !== null) {
                        val = match.querySelector("input[type=radio]:checked").value;
                    }
                    else {
                        val = "";
                    }
                    var obje = {};
                    var name = id; 
                    if (match.attributes["data-name"].value !== "") {
                        name = match.attributes["data-name"].value;
                    }
                    obje[name] = val;
                    Object.assign(multi_question_data, obje);
                }

                var text_question_data = {};
                for (var index = 0; index < trial.text_questions.length; index++) {
                    var id = "Q" + index;
                    var q_element = document
                        .querySelector("#jspsych-demographics-text-" + index)
                        .querySelector("textarea, input");
                    var val = q_element.value;
                    var name = q_element.attributes["data-name"].value;
                    if (name == "") {
                        name = id;
                    }
                    var obje = {};
                    obje[name] = val;
                    Object.assign(text_question_data, obje);
                }
 
                // save data
                var trial_data = {
                    rt: response_time,
                    multi_response: multi_question_data,
                    text_response: text_question_data,
                };
                display_element.innerHTML = "";
                // next trial
                this.jsPsych.finishTrial(trial_data);
            });
            var startTime = performance.now();
        }
    }
    DemographicsPlugin.info = info;
  
    return DemographicsPlugin;
  
  })(jsPsychModule);
  