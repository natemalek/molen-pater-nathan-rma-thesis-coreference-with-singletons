
function form_submitted2(evt) {
    if (is_submitted) {
        var json_str = JSON.stringify($('#form').serializeArray());
        $('#subinfo-annotations').val(json_str);
        $('#submission-info').slideDown(100);
    }
}

function copy_to_clipboard(evt) {
    $('#' + evt.data).select();
    document.execCommand("copy");
}

function close_submission(evt) {
    $('#submission-info').slideUp(100);
}

function switch_view(evt) {
    if ($('#view-pane').is(':visible')) {
        $('#view-pane').hide();
        $('#annotate-pane-wrapper').show();
    } else {
        $('#view-pane').show();
        $('#annotate-pane-wrapper').hide();
    }
}

function show_replay_dialog(evt) {
    $('#replay-dialog').show();
}

function close_replay_dialog(evt) {
    $('#replay-dialog').hide();
}

function replay(evt) {
    $('#replay-dialog').hide();
    var data = $.parseJSON($('#replay-events').val());
    var events_str = $.map(data, function(arr, idx) { 
        if (arr['name'] == 'events') { 
            return arr['value']; 
        } else {
            return ''; 
        } 
    }).join('');
    replay_events(events_str);
}

function setup2() {
    $('#btn_submit').click(form_submitted2);
    $("#subinfo-document-copy").click('subinfo-document', copy_to_clipboard);
    $("#subinfo-annotations-copy").click('subinfo-annotations', copy_to_clipboard);
    $('#btn_close_submission').click(close_submission);
    $('#btn_switch_view').click(switch_view);
    $('#btn_replay_dialog').click(show_replay_dialog);
    $('#btn_replay').click(replay);
    $('#btn_replay_close').click(close_replay_dialog);
}

$(document).ready(setup2);
