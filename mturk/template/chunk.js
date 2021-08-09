
/*
 * Adapted from "A Quick 'n Dirty Color Sequence"
 * http://ridiculousfish.com/blog/posts/colors.html
 */

function get_hue(idx) {
    /* Here we use 31 bit numbers because JavaScript doesn't have a 32 bit unsigned type, and so the conversion to float would produce a negative value. */
    var bitcount = 31;
    
    /* Reverse the bits of idx into ridx */
    var ridx = 0, i = 0;
    for (i=0; i < bitcount; i++) {
       ridx = (ridx << 1) | (idx & 1);
       idx >>>= 1;
    }
    
    /* Divide by 2**bitcount */
    var hue = ridx / Math.pow(2, bitcount);
    
    /* Start at .6 (216 degrees) */
    return (hue + .6) % 1;
}
 
var last_hue = 0;
function next_hue() {
    last_hue += 1;
    return get_hue(last_hue);
}
 
function reset_hue() {
    last_hue = 0
}

function next_degrees_readable() {
    var degrees;
    do {
        var hue = next_hue();
        degrees = Math.round(hue * 360);
    } while (degrees >= 50 && degrees <= 90);
    return degrees;
}
/*
 * End of "A Quick 'n Dirty Color Sequence"
 */


function show_target(target_stack, chains) {
    var showed;
    if (target_stack.length > 0) {
        var lead_elem = target_stack[target_stack.length-1];
        var target_chain = find_chain(lead_elem, chains);
        if (target_chain) {
            showed = target_chain;
        } else {
            showed = [lead_elem];
        }
    }
    $.each($('.mention'), function(idx, val) {        
        if ($.inArray(val, showed) > -1) {
            $(val).addClass('target');
        } else {
            $(val).removeClass('target');
        }
    });
}

function sort_targets(target_stack) {
    target_stack.sort(function(a, b){
        if ($.contains(a, b)) {
            return -1;
        } else if ($.contains(b, a)) {
            return 1;
        } else {
            return 0;
        }
    });
}

function remove_all_matches(val, arr) {
    for (i = arr.length-1; i >= 0; i--) {
        if (arr[i] == val) {
            arr.splice(i, 1);
        }
    }
}

function remove_chain(chain, chain_list, color_list) {
    for (i = chain_list.length-1; i >= 0; i--) {
        if (chain_list[i] == chain) {
            chain_list.splice(i, 1);
            color_list.splice(i, 1);
        }
    }
}

function is_skipped(elem) {
    return $.inArray(elem, skipped_expressions) > -1;
}

function find_chain(val, chains) {
    for (i = 0; i < chains.length; i++) {
        if ($.inArray(val, chains[i]) > -1) {
            return chains[i];
        }
    }
    return null;
}

function highlight_chain(selected_chain) {
    $.each($(".mention"), function(idx, val) {
        if ($.inArray(val, selected_chain) > -1) {
            $(val).addClass('selected');
        } else {
            $(val).removeClass('selected');
        }
    });
}

function add_to_set(val, arr) {
    if ($.inArray(val, arr) == -1) {
        arr.push(val);
    }
}

INSTRUCTIONS_COOKIE_NAME = 'nl.cltl.coreference.instructions_shown'

var saved_remembered_chains = []; // list(list(mention-DOM-elements))
var saved_remembered_colors = []; 
var remembered_chains = []; // list(list(mention-DOM-elements))
var skipped_expressions = []; // list(mention-DOM-elements)
var remembered_colors = []; 
var selected_chain = null;
var target_stack = [];
var is_grouping = false;
var annotation_events = [];
var start_time = new Date().getTime();
var sentence_elems; // store sentences here before displaying
var num_mentions = null;
var is_submitted = false;
var suppress_sentence_animation = false;

function add_annotation_event(name) {
    relative_time = new Date().getTime() - start_time;
    annotation_events.push([relative_time, name]);
}

function update_view(msg) {
	$('#btn_save_grouping').prop('disabled', !is_grouping);
    $('#btn_cancel_grouping').prop('disabled', !is_grouping);
    
	highlight_chain(selected_chain);
	$('.mention').each(function(idx, elem) {
		if (find_chain(elem, remembered_chains) || is_skipped(elem)) {
			$(elem).removeClass('todo');
		} else {
			$(elem).addClass('todo');
		}
    });
    if ($('.todo').length <= 0 && sentence_elems.length > 0) {
        show_next_sentence(true);
    }
    update_chain_identifiers_and_summary_pane();

    var can_skip_expression = (selected_chain != null) && (selected_chain.length == 1);
    $('#btn_skip_expression').prop('disabled', !can_skip_expression);

    update_notification(msg || '');
}

/**
 * Return an error message if the form is complete and can be submitted.
 * Otherwise, return an empty string.
 */
function check_if_form_is_complete() {
    add_annotation_event('submit');
    var num_shown_mentions = $('.mention').length;
    var num_annotated_mentions = num_shown_mentions - $('.todo').length;
    var num_remaining_mentions = num_mentions - num_annotated_mentions;
    if (num_remaining_mentions >= 2) {
        return "You have " + num_remaining_mentions + " more expressions to group.";
    } else if (num_remaining_mentions == 1) {
        return "You have one last expression to group.";
    }
    return "";
}

/**
 * Assign a color to a new chain if necessary while maintaining existing 
 * assignments stored in remembered_colors.
 */
function update_chain_color_assignments() {
    reset_hue(); // restart color sequence
    $.each(remembered_chains, function(chain_index, chain) {
        if (!remembered_colors[chain_index]) {
            var degrees;
            do {
                degrees = next_degrees_readable();
            } while ($.inArray(degrees, remembered_colors) != -1);
            remembered_colors[chain_index] = degrees;
        }
    });
}

function update_chain_identifiers_and_summary_pane() {
    var summary_pane = $('#summary')

    // clean things up
	summary_pane.empty();
    $('.chain-id').html('');
    $.each($('.mention'), function(idx, mention) {
        var mention_elem = $(mention);
        mention_elem.css("color", '');
        mention_elem.find('input').css("color", '');
    });

    update_chain_color_assignments();
    li_elems = []
    $.each(remembered_chains, function(chain_index, chain) {
        var chain_id = chain_index + 1;
        var chain_str = format_chain_readable(chain);
        var color_css_str = "hsl(" + remembered_colors[chain_index] + ", 100%, 50%)";

        // update summary pane
        li_elem = $('<li/>', {
            style: "color: " + color_css_str 
        });
        $.each(chain, function(idx, mention) {
            var text_spans = $(mention).find('.mention-text');
            var mention_text = $.map(text_spans, $.text).join(' ');
            if (idx > 0) {
                li_elem.append(' = ');
            }
            a_elem = $('<a/>', {
                href: '#' + mention.id
            });
            a_elem.append(mention_text);
            li_elem.append(a_elem);
        });
        li_elem.append(' ');
        button_elem = $('<button/>', {
            type: "button"
        });
        button_elem.append("delete");
        $(button_elem).click(function (evt) {
            if (confirm('Are you sure you want delete group ' + chain_id + '. ' + chain_str + '?')) {
                add_annotation_event('delete_group(' + format_chain(chain) + ')');
                remembered_chains.splice(chain_index, 1);
                remembered_colors.splice(chain_index, 1);
                save_remembered_chains();
                stop_grouping();
                update_view();
            }
        });
        li_elem.append(button_elem);
		li_elems.push(li_elem);

        // update color of expressions
        $.each(chain, function(idx, mention) {
            var mention_elem = $(mention);
            mention_elem.css("color", color_css_str);
            mention_elem.find('input').css("color", color_css_str);
            chain_id_elem = $('#' + mention_elem.attr('id') + '_chain_id');
            chain_id_elem.css("color", color_css_str);
        });
    });
    
    reversed = summary_pane.attr('reversed');
    if (typeof reversed !== typeof undefined && reversed !== false) {
        li_elems.reverse();
    }
    li_elems.forEach(function (li_elem) {summary_pane.append(li_elem);});

    // update chain identifiers last so that they don't show up in summary pane
    $.each(remembered_chains, function(chain_index, chain) {
        var chain_id = chain_index + 1;
        $.each(chain, function(idx, mention) {
            var mention_elem = $(mention);
            chain_id_elem = $('#' + mention_elem.attr('id') + '_chain_id');
            chain_id_elem.html('' + chain_id);
        });
	});
}

/**
 * Borrowed from:
 * https://stackoverflow.com/questions/3115982/how-to-check-if-two-arrays-are-equal-with-javascript
 */
function arraysEqual(a, b) {
    if (a === b) return true;
    if (a == null || b == null) return false;
    if (a.length != b.length) return false;
    for (var i = 0; i < a.length; ++i) {
      if (a[i] !== b[i]) return false;
    }
    return true;
}

/**
 * Return if A has the precedence over B.
 * For example, if precedence(A) > precedence(B) then B will be merged into A, i.e.
 * A stays (remain the same color) while B is removed (assume A's color).
 */
function has_precedence(chain_a, chain_b) {
    if (chain_a.length != chain_b.length) {
        return chain_a.length > chain_b.length;
    } else {
        idx_a = $.inArray(chain_a, remembered_chains);
        idx_b = $.inArray(chain_b, remembered_chains);
        return idx_a < idx_b;
    }
}

function add_chain_to_chain(removed_chain, kept_chain) {
    if (removed_chain == kept_chain) {
        return; // nothing to do
    }
    $.each(removed_chain, function(idx, val) {
        add_to_set(val, kept_chain);
        remove_all_matches(val, skipped_expressions);
    });
    remove_chain(removed_chain, remembered_chains, remembered_colors);
}

function handle_click_on_mention(evt) {
    // check that the current element is the top-most
    if (this != target_stack[target_stack.length-1]) {
        return;
    }
    if (is_grouping) {
    	evt.preventDefault();
        clicked_on_chain = find_chain(this, remembered_chains);
        if (clicked_on_chain) {
            if (arraysEqual(clicked_on_chain, selected_chain)) {
                // clicking on the selected chain --> remove unless it's a singleton
                if (clicked_on_chain.length >= 2) {
                    add_annotation_event('remove_mention(' + this.id + ', ' + format_chain(selected_chain) + ')');
                    remove_all_matches(this, selected_chain);
                } else {
                    add_annotation_event('clicked_on_singleton(' + this.id + ')');
                }
            } else {
                // one chain is selected, another is clicked on --> merge them together
                if (selected_chain) {
                    if (selected_chain.length < 3 || clicked_on_chain.length < 3 ||
                            confirm('You are about to merge one chain of ' + selected_chain.length + 
                            ' expressions and another of ' + clicked_on_chain.length + ' expressions, are you sure?\nThey are:\n- ' +
                            format_chain_readable(clicked_on_chain) + '\n- ' + format_chain_readable(selected_chain))) {
                        var kept_chain, removed_chain;
                        if (has_precedence(clicked_on_chain, selected_chain)) {
                            kept_chain = clicked_on_chain; removed_chain = selected_chain; 
                        } else {
                            kept_chain = selected_chain; removed_chain = clicked_on_chain;
                        }
                        add_annotation_event('add_chain_to_chain(' + format_chain(removed_chain) + ',' + format_chain(kept_chain) + ')');
                        add_chain_to_chain(removed_chain, kept_chain);
                        selected_chain = kept_chain;
                    } else {
                        stop_grouping();
                    }
                } else {
                    add_annotation_event('select_chain(' + format_chain(clicked_on_chain) + ')');
                    selected_chain = clicked_on_chain;
                }
            }
        } else {
            // clicked on a stand-alone mention --> add it to the selected chain
            add_annotation_event('add_mention_to_chain(' + this.id + ', ' + format_chain(selected_chain) + ')');
            add_to_set(this, selected_chain);
            remove_all_matches(this, skipped_expressions);
        }
    } else {
        // switch to another chain
        var new_selected_chain = find_chain(this, remembered_chains);
        var is_new_singleton = (new_selected_chain == null);
        if (is_new_singleton) {
            new_selected_chain = [this];
        }
        if (arraysEqual(new_selected_chain, selected_chain)) {
            add_annotation_event('unselect_chain(' + format_chain(clicked_on_chain) + ')');
            selected_chain = null;
        } else {
            start_grouping();
            selected_chain = new_selected_chain;
            remove_all_matches(selected_chain[0], skipped_expressions);
            if (is_new_singleton) {
                add_annotation_event('add_singleton(' + format_chain(selected_chain) + ')');
                remembered_chains.push(selected_chain);
            } else {
                add_annotation_event('select_chain(' + format_chain(new_selected_chain) + ')');
            }
        }
    }
    update_view();
}

$.urlParam = function (name) {
    var results = new RegExp('[\?&]' + name + '=([^&#]*)')
                      .exec(window.location.href);
    if (results) {
    	return results[1];
    } else {
    	return '';
    }
}

function copy_chains(src) {
    return $.map(src, function (chain, idx) {
        var shallow_copy = $.extend([], chain);
        return [ shallow_copy ]; // wrapped to avoid flattening
    });
}

function save_remembered_chains() {
    // always perform a copy here otherwise saved_remembered_chains will be
    // spookily updated via remembered_chains
    saved_remembered_chains = copy_chains(remembered_chains);
    saved_remembered_colors = $.extend([], remembered_colors);
}

function restore_remembered_chains() {
    // always perform a copy here otherwise saved_remembered_chains will be
    // spookily updated via remembered_chains
    remembered_chains = copy_chains(saved_remembered_chains);
    remembered_colors = $.extend([], saved_remembered_colors);
}

function save_grouping(evt) {
    add_annotation_event('save_grouping');
    if (Math.random() < 0.1) {
        var chain_str = format_chain_readable(selected_chain);
        var confidence_prompt = "Please rate your confidence for the "
        if (selected_chain.length >= 2) {
            confidence_prompt += 'group "' + chain_str + '"';
        } else {
            confidence_prompt += 'singleton group "' + chain_str + '"';
        }
        confidence_prompt += ".\nEnter a number between 0 (not confident) and 5 (absolutely certain)."
        var confidence_level = prompt(confidence_prompt).trim();
        add_annotation_event('confidence:' + confidence_level);
        if ($.inArray(confidence_level, ['0', '1', '2', '3', '4', '5']) > -1) {
            save_remembered_chains();
            stop_grouping();
            update_view('Your confidence level was recorded: ' + confidence_level + '.');
        } else {
            cancel_grouping();
            update_view("Confidence level is invalid, the grouping action was canceled.");
        }
    } else {
        save_remembered_chains();
        stop_grouping();
        update_view('');
    }
}

// this function is called by other functions only
function start_grouping() {
    add_annotation_event('start_grouping');
    is_grouping = true;
    $('#annotate-pane').addClass('linking');
}

// this function is called by other functions only
function stop_grouping() {
    is_grouping = false;
    $('#annotate-pane').removeClass('linking');
    selected_chain = null;
}

function cancel_grouping(evt) {
    add_annotation_event('cancel_grouping');
    selected_chain = null;
    restore_remembered_chains();
    stop_grouping();
    update_view();
}

function skip_expression(evt) {
    add_annotation_event('skip_expression');
    add_to_set(selected_chain[0], skipped_expressions);
    remove_chain(selected_chain, remembered_chains, remembered_colors);
    selected_chain = null;
    stop_grouping();
    save_remembered_chains();
    update_view();
}

function display_instructions(evt) {
    add_annotation_event('display_instructions');
    $('#instructions').slideDown(100);
    Cookies.set(INSTRUCTIONS_COOKIE_NAME, 'true', { expires: 1 });
}

function close_instructions(evt) {
    add_annotation_event('close_instructions');
    $('#instructions').slideUp(100);
}

function surpress_hot_keys(evt) {
    if (evt.key >= 'a' && evt.key <= 'z') {
        evt.stopPropagation();
    }
}

function resove_input_event_ambiguity(evt) {
    if (is_grouping) {
        evt.preventDefault();
    } else {
        evt.stopPropagation();
    }
}

function format_chain(chain) {
    // slice() is here to prevent the quadratic increase of the event JSON string
    // if the event string is too lengthy, it won't fit any Google form
    return $.map(chain.slice(0, 2), function (elem, idx) {
        return elem.id;
    }).join('=');
}

function format_chain_full(chain) {
    // slice() is here to prevent the quadratic increase of the event JSON string
    // if the event string is too lengthy, it won't fit any Google form
    return $.map(chain, function (elem, idx) {
        return elem.id;
    }).join('=');
}

function format_chain_readable(chain) {
    return $.map(chain, function (elem, idx) {
        var text_spans = $(elem).find('.mention-text');
        return $.map(text_spans, $.text).join(' ');
    }).join(' = ')
}

function fill_dynamic_fields() {
    // fill the field #chains
    chains_str = $.map(remembered_chains, format_chain_full).join(',');
    $('#chains').val(chains_str);
    // fill the field #blanks
    var edited_blanks = $('.blank').filter(function (idx, blank) {
        var filtered_chars = $.text(blank).split('').filter(function(value, idx, arr) {
            return value != '_'
        });
        return filtered_chars.length > 0;
    });
    var blanks_str = $.map(edited_blanks, function (blank, idx) {
            return blank.id + '=' + $.text(blank);
        }).join(',');
    $('#blanks').val(blanks_str);
    // fill the field #events
    annotation_events_str = $.map(annotation_events, function (ann_evt) {
        return ann_evt[0] + ":" + ann_evt[1];
    }).join(';');
    $('#events').val(annotation_events_str)
}

function update_notification(msg) {
    $('#notification').hide();
    if (msg == '') {
        $('#notification-wrapper').removeClass('highlighted');
    } else {
        $('#notification-wrapper').addClass('highlighted');
        $('#notification').html(msg).fadeIn(800);
    }
}

function form_submitted(evt) {
    msg = check_if_form_is_complete();
    update_view(msg);
    if (msg == '') {
        fill_dynamic_fields();
        is_submitted = true;
    } else {
    	evt.preventDefault();
        is_submitted = false;
    }
}

function update_sentence_counter_with_message(msg) {
    $("#sentence-counter").text(msg);
}

function update_sentence_counter() {
    if (sentence_elems.length >= 2) {
        update_sentence_counter_with_message(sentence_elems.length + ' more sentences');
    } else if (sentence_elems.length == 1) {
        update_sentence_counter_with_message('1 last sentence');
    } else {
        update_sentence_counter_with_message('END');
    }
}

function show_next_sentence(animated) {
    var sent = sentence_elems.shift();
    $('#annotate-pane').append(sent);
    if (animated && !suppress_sentence_animation) {
        $(sent).delay(1000).fadeIn(1200, update_sentence_counter);
    } else {
        $(sent).show();
        update_sentence_counter();
    }
    // only when the objects are in DOM that we can add events
    $(sent).find(".mention").hover(
        function() {
            target_stack.push(this);
            sort_targets(target_stack);
            // show_target(target_stack, remembered_chains);
        }, function() {
            remove_all_matches(this, target_stack);
            // show_target(target_stack, remembered_chains);
        }
    );
    $(sent).find(".mention").click(handle_click_on_mention);
    update_view();
}

function reset_all() {
    saved_remembered_chains = []; // list(list(mention-DOM-elements))
    saved_remembered_colors = []; 
    remembered_chains = []; // list(list(mention-DOM-elements))
    skipped_expressions = []; // list(mention-DOM-elements)
    remembered_colors = []; 
    selected_chain = null;
    target_stack = [];
    is_grouping = false;
    annotation_events = [];
    start_time = new Date().getTime();
    sentence_elems; // store sentences here before displaying
    num_mentions = null;
    is_submitted = false;
    $(document).clearQueue();
}

function replay_events(all_events_str, delay_ms) {
    reset_all();
    var events = all_events_str.split(';').map(function(s) { return s.split(':')[1]; });
    suppress_sentence_animation = true;
    events.forEach(function (evt_str) { replay_event(evt_str, delay_ms); });
    $(document).queue(function(next) {
        suppress_sentence_animation = false;
        // put back the events
        annotation_events = all_events_str.split(';').map(function(s) {
            parts = s.split(':');
            return [parts[0], parts.slice(1).join(':')]
        });
        last_recorded_relative_time = annotation_events[annotation_events.length-1][0];
        start_time = new Date().getTime() - last_recorded_relative_time;
        next();
    });
}

function replay_event(evt_str, delay_ms) {
    if (evt_str == 'start_grouping' || evt_str == 'submit' || evt_str == 'confidence' ||
        evt_str == 'display_instructions' || evt_str == 'close_instructions' ||
        evt_str.startsWith('clicked_on_singleton') || evt_str.startsWith('select_chain') || 
        evt_str == 'unselect_chain') {
        // ignore
    } else {
        var f;
        if (evt_str.startsWith('add_singleton')) {
            var match = /add_singleton\((\w+)(?:=\w+)*\)/.exec(evt_str);
            f = function(next) {
                var selected_elem = document.getElementById(match[1]);
                if (!find_chain(selected_elem, remembered_chains)) {
                    console.assert(selected_elem != null, "Element not found: %s", match[1]);
                    start_grouping();
                    remove_all_matches(selected_elem, skipped_expressions);
                    remembered_chains.push([selected_elem]);
                    update_view();
                }
                next();
            };
        } else if (evt_str.startsWith('add_mention_to_chain')) {
            var match = /add_mention_to_chain\((\w+),\s*(\w+)(?:=\w+)*\)/.exec(evt_str);
            f = function(next) {
                var selected_elem = document.getElementById(match[1]);
                var active_chain = find_chain(document.getElementById(match[2]), remembered_chains);
                console.assert(selected_elem != null, "Element not found: %s", match[1]);
                console.assert(active_chain != null, "Chain not found for element %s", match[2]);
                add_to_set(selected_elem, active_chain);
                remove_all_matches(selected_elem, skipped_expressions);
                update_view();
                next();
            };
        } else if (evt_str.startsWith('remove_mention')) {
            var match = /remove_mention\((\w+),\s*(\w+)(?:=\w+)*\)/.exec(evt_str);
            f = function(next) {
                var selected_elem = document.getElementById(match[1]);
                var active_chain = find_chain(document.getElementById(match[2]), remembered_chains);
                console.assert(selected_elem != null, "Element not found: %s", match[1]);
                console.assert(active_chain != null, "Chain not found for element %s", match[2]);
                remove_all_matches(selected_elem, active_chain);
                update_view();
                next();
            };
        } else if (evt_str.startsWith('add_chain_to_chain')) {
            var match = /add_chain_to_chain\((\w+)(?:=\w+)*,\s*(\w+)(?:=\w+)*\)/.exec(evt_str);
            f = function(next) {
                var removed_chain = find_chain(document.getElementById(match[1]), remembered_chains);
                var kept_chain = find_chain(document.getElementById(match[2]), remembered_chains);
                console.assert(removed_chain != null, "Chain not found for element %s", match[1]);
                console.assert(kept_chain != null, "Chain not found for element %s", match[2]);
                add_chain_to_chain(removed_chain, kept_chain);
                update_view();
                next();
            };
        } else if (evt_str == 'skip_expression') {
            f = function(next) {
                skip_expression;
                next();
            }
        } else if (evt_str == 'save_grouping') {
            f = function(next) {
                save_remembered_chains();
                stop_grouping();
                update_view('');
                next();
            };
        } else if (evt_str == 'cancel_grouping') {
            f = function(next) {
                cancel_grouping();
                update_view('');
                next();
            };
        } else {
            console.assert(false, "Unknown event: %s", evt_str);
        }
        if (delay_ms) {
            $(document).delay(delay_ms);
        }
        $(document).queue(f);
    }
}

function setup() {
    $('textarea').keypress(surpress_hot_keys);
    $('.blank').click(resove_input_event_ambiguity);
    $('.blank').keypress(resove_input_event_ambiguity);
	$(document).keypress(function (evt) {
        var target_tag = $(evt.target).prop('tagName');
        if ((evt.key == 'Enter' || evt.key == ' ') && target_tag != 'TEXTAREA') {
            save_grouping(evt);
            evt.preventDefault();
        }    
    });
    num_mentions = $('.mention').length;
    sentence_elems = $('.sentence').toArray();
    // hide() before remove() so that they will be appended as hidden
    $('.sentence').hide().remove(); 
    show_next_sentence(false); // animated = false
    
    // toolbar
    $('#btn_save_grouping').click(save_grouping);
    $('#btn_cancel_grouping').click(cancel_grouping);
    $('#btn_skip_expression').click(skip_expression);

    $('#btn_display_instructions').click(display_instructions);
    $('#btn_close_instructions').click(close_instructions);
    $('.blank').focusout(update_view);
    
    // form
    $('#btn_submit').click(form_submitted);
    $('#form').append('<input type="hidden" value="' + $.urlParam('assignmentId') + '" name="assignmentId"/>');
    $('#form').append('<input type="hidden" value="' + $.urlParam('workerId') + '" name="workerId"/>');
    $('#form').append('<input type="hidden" value="' + $.urlParam('hitId') + '" name="hitId"/>');
    $('#form').append('<input type="hidden" name="chains" id="chains"/>');
    update_view();

    $(window).on('beforeunload', function(evt) {
        if (saved_remembered_chains.length >= 1 && !is_submitted) {
            return "You have unsubmitted annotations. They will be lost if you leave this page. Are you sure?";
        }
    }); 

    if (!Cookies.get(INSTRUCTIONS_COOKIE_NAME)) {
        display_instructions();
    }
}

$(document).ready(setup);
