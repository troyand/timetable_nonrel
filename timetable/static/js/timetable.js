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

function isNonNegativeNumber(n) {
    var p = parseInt(n);
    if (isNaN(p)) {
        return false;
    }
    if (p >= 0) {
        return true;
    }
    else {
        return false;
    }
}

function validateWeeksRange(range) {
    if (range == "") {
        return false;
    }
    var parts = range.split(",");
    for (var i=0; i<parts.length; i++) {
        var part = parts[i];
        if (part == "") {
            return false;
        }
        if (part.indexOf("-") != -1) {
            weekNumbers = part.split("-");
            if (weekNumbers.length != 2) {
                return false;
            }
            if (! isNonNegativeNumber(weekNumbers[0])) {
                return false;
            }
            if (! isNonNegativeNumber(weekNumbers[1])) {
                return false;
            }
        }
        else {
            if (! isNonNegativeNumber(part)) {
                return false;
            }
        }
    }
    return true;
}

function serializeItems() {
    var result = [];
    errorsFound = false;
    $.each($(".item"), function(i, formItem) {
        var item = {};
        var itemElement = $(formItem);
        var divId = itemElement.parent().attr("id");
        var idParts = divId.split("-");
        item["day_number"] = parseInt(idParts[1]);
        item["lesson_number"] = parseInt(idParts[2]);
        itemElement.removeClass("has-error");
        if (!validateWeeksRange(itemElement.find(".weeks").val()) || itemElement.find(".discipline").val() == "") {
            itemElement.addClass("has-error");
            errorsFound = true;
        }
        $.each(["room", "discipline", "group", "lecturer", "weeks"], function(j, field) {
            item[field] = itemElement.find("." + field).val() || null;
        });
        result.push(item);
    });
    if (errorsFound) {
        $("html, body").animate({
            scrollTop: $($(".has-error")[0]).offset().top
        }, 500);
        throw "Validation error";
    }
    return JSON.stringify(result);
}

function attachAutocomplete(node) {
    node.find(".room").autocomplete({
        serviceUrl:"/autocomplete/rooms/",
        minChars:1,
    });
    /*node.find(".discipline").autocomplete({
        serviceUrl:"/autocomplete/disciplines/",
        minChars:1,
    });*/
    node.find(".lecturer").autocomplete({
        serviceUrl:"/autocomplete/lecturers/",
        minChars:1,
    });
}


function validateWeeksInputKey(evt) {
    var charCode = (evt.which) ? evt.which : event.keyCode;
    console.log(charCode);
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
    if (charCode == 8) {
        // is a backspace
        return true;
    }
    if (charCode == 99) {
        // copy
        return true;
    }
    if (charCode == 118) {
        // paste
        return true;
    }
    return false;
}

var copied = null;

function copyLesson(sender) {
    if (copied) {
        copied.remove();
    }
    copied = $(sender).parent().clone().hide();
    copied.find(".discipline").val($(sender).parent().find(".discipline").val());
}

function pasteLesson(sender) {
    var local = copied;
    copied = local.clone();
    copied.find(".discipline").val(local.find(".discipline").val());
    local.show();
    attachAutocomplete(local);
    $(sender).parent().parent().find(".items").append(local);
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

