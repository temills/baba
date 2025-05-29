var jsPsychRepeatedGeneration = (function (jspsych) {
  'use strict';

    const info = {
        name: "repeated-generation",
        parameters: {
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
     * **repeated-generation**
     *
     * jsPsych plugin for free text response survey questions
     *
     * @author Josh de Leeuw
     * @see {@link https://www.jspsych.org/plugins/jspsych-repeated-generation/ repeated-generation plugin documentation on jspsych.org}
     */
    class RepeatedGenerationPlugin {
        constructor(jsPsych) {
            this.jsPsych = jsPsych;
        }
        trial(display_element, trial) {
            var response_boxes = [];
            /*
            var response_boxes = [];
            for (var i = 0; i < response_boxes.length; i++) {
                response_boxes[i].rows = 1;
                response_boxes[i].columns = 40;
                response_boxes[i].value = "";
            }
            */

            var html = "";
            // show preamble text
            if (trial.preamble !== null) {
                html +=
                    '<div id="jspsych-repeated-generation-preamble" class="jspsych-repeated-generation-preamble">' +
                        trial.preamble +
                        "</div>";
            }
            // start form
            if (trial.autocomplete) {
                html += '<form id="jspsych-repeated-generation-form">';
            }
            else {
                html += '<form id="jspsych-repeated-generation-form" autocomplete="off">';
            }
            html += '<input type="text" id="0" class="text-box">'

            html += '<div id="before_button"><br></br><div>'
            html += '<input type="submit" id="jspsych-repeated-generation-next" class="jspsych-btn jspsych-survey-text" value="' +
            trial.button_label +
            '"></input>';
            html += "</form>";
            display_element.innerHTML = html;


           
            function getTextFromTextBoxes() {
                const textBoxes = document.querySelectorAll('.text-box');
                const textBoxValues = [];
                textBoxes.forEach(textBox => {
                    textBoxValues.push(textBox.value);
                });
                return textBoxValues;
            }
            var text_box_num = 0;
            //for each textbox, when created
            //for each textbox, when typing started
            var rts = []
            // Function to handle the keydown event
            function createTextBox() {
                const newTextBox = document.createElement('input');
                newTextBox.type = 'text';
                text_box_num = text_box_num +1;
                newTextBox.id = text_box_num;
                var t = performance.now();
                if (rts.length < text_box_num+1) {
                    rts.push([])
                }
                rts[text_box_num].push(t)
                newTextBox.className = 'text-box';
                newTextBox.addEventListener('keydown', handleKeyPress);
                return newTextBox;
            }

            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    event.preventDefault();  // Prevent the default action of the Enter key
                    if (prev_box.value.trim() !== '') {
                        var linebreak1 = document.createElement('br');
                        const newTextBox = createTextBox();


                        event.target.parentNode.insertBefore(linebreak1, document.getElementById("before_button"));
                        event.target.parentNode.insertBefore(newTextBox, document.getElementById("before_button"));
                        newTextBox.focus();  // Focus on the new text box
                        prev_box=newTextBox;
                    }
                } else {
                    if (rts[text_box_num].length < 2) {
                        var t = performance.now()
                        rts[text_box_num].push(t)
                    }
                }
            }
                
            const initialTextBox = document.querySelector('.text-box');
            var prev_box = initialTextBox;
            function addEventListeners() {
                //document.getElementById('content').appendChild(createButton());
                //document.addEventListener('keydown', handleKeyPress);
                //initialTextBox = document.querySelector('.text-box');
                initialTextBox.addEventListener('keydown', handleKeyPress);
                //initialTextBox.addEventListener('mousedown', handleClick);
                var startTime = performance.now();
                rts.push([startTime])
                initialTextBox.focus();
            }
                

            if (document.readyState === 'complete' || document.readyState === 'interactive') {
                // If the document is already ready, call addEventListeners immediately
                addEventListeners();
            } else {
                // Otherwise, wait for the DOM to be fully loaded
                document.addEventListener('DOMContentLoaded', function() {
                  addEventListeners();
                });
            }

            // add submit button
            /*

            */

            // backup in case autofocus doesn't work
            //display_element.querySelector("#input-" + question_order[0]).focus();

            
            display_element.querySelector("#jspsych-repeated-generation-form").addEventListener("submit", (e) => {
                e.preventDefault();
                // measure response time
                /*
                var endTime = performance.now();
                var response_time = Math.round(endTime - startTime);
                // create object to hold responses
                var question_data = {};
                for (var index = 0; index < trial.questions.length; index++) {
                    var id = "Q" + index;
                    var q_element = document
                        .querySelector("#jspsych-repeated-generation-" + index)
                        .querySelector("textarea, input");
                    var val = q_element.value;
                    var name = q_element.attributes["data-name"].value;
                    if (name == "") {
                        name = id;
                    }
                    var obje = {};
                    obje[name] = val;
                    Object.assign(question_data, obje);
                }
                */
                // save data
                var trialdata = {
                    rts: rts,//response_time,
                    responses: getTextFromTextBoxes(),
                };
                display_element.innerHTML = "";
                // next trial
                this.jsPsych.finishTrial(trialdata);
            });
        
        }
    }
    RepeatedGenerationPlugin.info = info;

    return RepeatedGenerationPlugin;

})(jsPsychModule);
