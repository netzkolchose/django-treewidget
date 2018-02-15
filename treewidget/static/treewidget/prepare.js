if (!window.jQuery) {
    if (window.django.jQuery) {
        window.jQuery = window.django.jQuery;
        window.reverse_jquery = true;
    } else {
        throw new Error('need jquery for jstree');
    }
}
