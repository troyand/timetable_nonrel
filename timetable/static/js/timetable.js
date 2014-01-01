function validateWeeksInputKey(evt) {
    var charCode = (evt.which) ? evt.which : event.keyCode;
    if ((charCode >= 48) && (charCode <= 57)) {
        // is a digit
        return true;
    }
    if (charCode == 44) {
        // is a comma
        return true;
    }
    if (charCode == 45) {
        // is a dash
        return true;
    }
    return false;
}

function addLesson(sender) {
    var clone = $("#clonable-item").clone().show();
    clone.insertBefore($(sender));
    clone.find(".room").autocomplete({
        serviceUrl:"/autocomplete/rooms/",
        minChars:1,
    });
}

function deleteLesson(sender) {
    $(sender).parent().remove();
}

function goRenderTimetable(csrfToken) {
    var selected = $(".group-input:checked");
    var serialized = [];
    $.each(selected, function(i, item) {
        var jqItem = $(item);
        serialized.push([jqItem.data("timetable-id"), jqItem.data("discipline"), jqItem.data("group") ? jqItem.attr("data-group") : null]);
    });
    $.post("/get-link/", {
        csrfmiddlewaretoken: csrfToken,
        groups: JSON.stringify(serialized)
    }).done(function(data) {
            window.location.href = '/render/' + data + '/';
    });
}

function goIcalTimetable(csrfToken) {
    var selected = $(".group-input:checked");
    var serialized = [];
    $.each(selected, function(i, item) {
        var jqItem = $(item);
        serialized.push([jqItem.data("timetable-id"), jqItem.data("discipline"), jqItem.data("group") ? jqItem.attr("data-group") : null]);
    });
    $.post("/get-link/", {
        csrfmiddlewaretoken: csrfToken,
        groups: JSON.stringify(serialized)
    }).done(function(data) {
        $("#ical-link").attr("href", "/ical/" + data + "/").show();
    });
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');

function enrollment(label) {
    var jqItem = $(label);
    var url = "";
    if (jqItem.hasClass("active")) {
        url = "/unenroll/";
    }
    else {
        url = "/enroll/";
    }
    url += jqItem.data("timetable-id") + "/";
    url += jqItem.data("discipline") + "/";
    url += jqItem.data("group") + "/";
    $.post(url, {
        csrfmiddlewaretoken: csrftoken
    }).done(function(data) {
        return;
    });
}

