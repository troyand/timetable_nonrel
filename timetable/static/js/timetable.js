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
