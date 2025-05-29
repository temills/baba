/**
 * jspsych-audio-safari-init
 * Etienne Gaudrain
 *
 * Safari is the new Internet Explorer and does everything differently from others
 * for better, and mostly for worse. Here is a plugin to display a screen for the user to click on
 * before starting the experiment to unlock the audio context, if we are dealing with Safari.
 *
 **/

var jsPsychAudioSafariInit = (function (jspsych) {
    'use strict';

    //jsPsych.pluginAPI.registerPreload('audio-safari-init', 'stimulus', 'audio');

    const info = {
        name: 'audio-safari-init',
        description: '',
        parameters: {
            prompt: {
                type: jspsych.ParameterType.STRING,
                pretty_name: 'Prompt',
                default: "Click on the screen to start the experiment",
                description: 'The prompt asking the user to click on the screen.'
            }
        }
    }

    class AudioSafariInitPlugin {
        constructor(jsPsych) {
            this.jsPsych = jsPsych;
        }
        trial(display_element, trial, on_load) {

            // Ideally, we would want to be able to detect this on feature basis rather than using userAgents,
            // but Safari just doesn't count clicks not directly aimed at starting sounds, while other browsers do.
            const is_Safari = true///Version\/.*Safari\//.test(navigator.userAgent) && !window.MSStream;
            if(is_Safari){
                display_element.innerHTML = trial.prompt;
                document.addEventListener('touchstart', init_audio);
                document.addEventListener('click', init_audio);
            } else {
                jsPsych.finishTrial();
            }

            function init_audio(){
                jsPsych.pluginAPI.audioContext();
                end_trial();
            }

            // function to end trial when it is time
            function end_trial() {

                document.removeEventListener('touchstart', init_audio);
                document.removeEventListener('click', init_audio);

                // kill any remaining setTimeout handlers
                jsPsych.pluginAPI.clearAllTimeouts();

                // kill keyboard listeners
                jsPsych.pluginAPI.cancelAllKeyboardResponses();

                // clear the display
                display_element.innerHTML = '';

                // move on to the next trial
                jsPsych.finishTrial();
            }


        };
    }
    AudioSafariInitPlugin.info = info;

    return AudioSafariInitPlugin;
      
})(jsPsychModule);
      