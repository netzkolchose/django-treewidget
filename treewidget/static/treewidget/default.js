(function($) {
    function pk_proto(prefix, attr_name) {
        var pre = [prefix, attr_name, ''].join('_');
        return function(id) {
            if (!id || id === '#')
                return '#';
            return pre + id;
        }
    }

    $(document).on('move_error.treewidget', function() {
        alert('Error while moving node!');
    });

    $(document).ready(function() {
        $('.treewidget').each(function(idx, el) {
            var $el = $(el);
            var data_element = $el.children('script')[0];
            var data = JSON.parse(data_element.textContent || data_element.innerText);
            var treedata = data.treedata;
            var settings = data.settings;
            var additional = data.additional;
            var attr_name = additional.id;
            var pk = pk_proto('treewidget', attr_name);

            // set treedata
            if (treedata) {
                var core = settings.core || {};
                core.data = treedata;
                settings.core = core;
            }

            // widget is disabled
            if (additional.disabled) {
                //$el.addClass('treewidget-disabled');  // TODO: move to template
                $el.on('ready.jstree', function() {
                    $($el.jstree(true).get_json('#', { flat: true })).each(function() {
                        $el.jstree("disable_node", this.id);
                    });
                });
            } else {
                // select/deselect standard handler to update django options
                $el.on('select_node.jstree', function(e, data){
                    var selected = $('#treewidget_' + attr_name).jstree('get_selected');
                    // clear 'em all
                    $('#' + attr_name + ' option').each(function(idx, el) {
                        el.selected = false;
                    });
                    // set selected
                    selected.forEach(function(el) {
                        $('#' + attr_name + ' option[value="' + el.split('_').pop() + '"]')[0].selected = true;
                    });
                    $('#' + attr_name).change();
                });
                $el.on('deselect_node.jstree', function(e, data){
                    $('#' + attr_name + ' option[value="' + data.node.id.split('_').pop() + '"]')[0].selected = false;
                    $('#' + attr_name).change();
                });
            }

            // additional button handlers
            if (additional.show_buttons) {
                $('#treewidget-container_' + attr_name + ' a.expand').on('click', function () {
                    $el.jstree('open_all');
                });
                $('#treewidget-container_' + attr_name + ' a.collapse').on('click', function () {
                    $el.jstree('close_all');
                });
                $('#treewidget-container_' + attr_name + ' a.selected').on('click', function () {
                    $el.jstree('close_all');
                    var selected = $el.jstree('get_selected', true);
                    for (var i = 0; i < selected.length; ++i)
                        $el.jstree()._open_to(selected[i].id);
                });
            }

            // add plugins as needed
            var plugins = settings.plugins || [];
            settings.plugins = plugins;

            // search plugin & search function
            if (additional.search) {
                if (plugins.indexOf('search') === -1)
                    plugins.push('search');
                var to = null;
                $('#treewidget-search_' + attr_name).keyup(function () {
                    if (to) clearTimeout(to);
                    to = setTimeout(function () {
                        var v = $('#treewidget-search_' + attr_name).val();
                        $el.jstree(true).search(v);
                    }, 250);
                });
            }

            // sort plugin & sort function
            if (additional.sort.length) {
                if (plugins.indexOf('sort') === -1)
                    plugins.push('sort');
                settings.sort = function(a, b) {
                    var data_a = this.get_node(a).data.sort;
                    var data_b = this.get_node(b).data.sort;
                    for (var i=0; i<additional.sort.length; ++i) {
                        if (data_a[i] === data_b[i])
                            continue;
                        return ((data_a[i] > data_b[i]) ? 1 : -1) * additional.sort[i];
                    }
                    return (a.text > b.text) ? 1 : -1;
                };
            }

            // drag'n drop plugin & move handler
            if (additional.dnd) {
                if (plugins.indexOf('dnd') === -1)
                    plugins.push('dnd');
                if (additional.moveurl) {
                    var move_node_handler = function (ev, data) {
                        var parent_node = $el.jstree('get_node', data.parent);
                        var position = parent_node.children.indexOf(data.node.id);
                        var prev = null;
                        if (position > 0)
                            prev = parent_node.children[position - 1].split('_').slice(-1)[0];
                        var next = null;
                        if (position + 1 < parent_node.children.length)
                            next = parent_node.children[position + 1].split('_').slice(-1)[0];
                        $.getJSON(
                            additional.moveurl,
                            $.param({
                                appmodel: additional.appmodel,
                                id: data.node.id.split('_').slice(-1)[0],
                                parent: (data.parent === '#') ? null : data.parent.split('_').slice(-1)[0],
                                prev: prev,
                                next: next
                            }, true),
                            function (resp) {
                                if (resp)
                                    return;
                                // revert to last state
                                $el.off('move_node.jstree', move_node_handler);
                                $el.jstree('move_node', data.node, data.old_parent, data.old_position);
                                $('#'+data.node.id).trigger('move_error.treewidget', [data]);
                                $el.on('move_node.jstree', move_node_handler);
                            }
                        );
                    };
                    $el.on('move_node.jstree', move_node_handler);
                }
            }

            // init jstree
            $el.jstree(settings);
            $el.jstree().settings.core.multiple = additional.multiple;

            // exit here if we cant update elements
            if (!additional.updateurl || additional.disabled)
                return;

            // get all known options
            var all_options = [];
            $('#'+attr_name+' option').each(function() {all_options.push(this.value);});
            var all_texts = {};
            $('#'+attr_name+' option').each(function() {
                $(this).text('#' + $(this).text());
                all_texts[this.value] = $(this).text();
            });

            // updates for name or position changes
            var name_handler = function(ev) {
                if (ev.target !== $('#'+attr_name)[0]) {
                    // only operate on option elements
                    if (ev.target.nodeName.toLowerCase() !== 'option')
                        return;
                    // popup did not return anything useful if text was not changed
                    if (all_texts[ev.target.value] === ev.target.text)
                        return;

                    // update all_texts
                    // to spot another change on the same option we have to customize the text again
                    var txt = ev.target.text;
                    all_texts[ev.target.value] = '#' + txt;
                    ev.target.text = '#' + txt;

                    var tree_items = $el.jstree(true).get_json('#', { flat: true }).map(
                        function(el) { return el.id; }
                    );

                    // update from popup rename/move
                    $.getJSON(
                        additional.updateurl,
                        $.param({
                            appmodel: additional.appmodel,
                            ids: [ev.target.value],
                            sort: (additional.sort.length) ? 1 : 0
                        }, true),
                        function (resp) {

                            // since tree could have changed in between get nodes again
                            var tree_items = $el.jstree(true).get_json('#', { flat: true }).map(
                                function(el) { return el.id; }
                            );

                            for (var i=0; i < resp.length; ++i) {
                                var data = resp[i];

                                // first check if node has still same parent to skip parent inserts
                                var new_parent = pk(data.parent);
                                var old_node = $el.jstree(true).get_node(pk(data.id));
                                if (old_node) {
                                    if (new_parent === old_node.parent) {
                                        $el.jstree('rename_node', old_node, data.name);
                                        old_node.data.sort = data.sort;
                                        continue;
                                    }
                                }

                                // check if parent node exists, add node if not
                                for (var j=0; j<data.parents.length; ++j) {
                                    if (tree_items.indexOf(pk(data.parents[j].id)) === -1) {
                                        $el.jstree().create_node(
                                            pk(data.parents[j].parent),
                                            {
                                                id: pk(data.parents[j].id),
                                                text: data.parents[j].name,
                                                state: {selected: false},
                                                data: {sort: data.sort}
                                            },
                                            'last'
                                        );
                                    }
                                }

                                // try to move node
                                if (old_node) {
                                    $el.off('move_node.jstree', move_node_handler);
                                    var done = false;
                                    if (data.prev) {
                                        var prev = $el.jstree(true).get_node(pk(data.prev));
                                        if (prev) {
                                            $el.jstree('move_node', old_node, prev, 'after');
                                            done = true;
                                        }
                                    } else if (!done && data.next) {
                                        var next = $el.jstree(true).get_node(pk(data.next));
                                        if (next) {
                                            $el.jstree('move_node', old_node, next, 'before');
                                            done = true;
                                        }
                                    } else if (!done) {
                                        $el.jstree('move_node', old_node, new_parent, 'last');
                                    }
                                    $el.on('move_node.jstree', move_node_handler);
                                    continue;
                                }

                                // should not end up here
                                // must delete old node first
                                $el.jstree('delete_node', pk(data.id));

                                // insert node into tree
                                $el.jstree().create_node(
                                    pk(data.parent),
                                    {
                                        id: pk(data.id),
                                        text: data.name,
                                        state: {selected: true},
                                        data: {sort: data.sort}
                                    },
                                    'last'
                                );
                                $el.jstree()._open_to(pk(data.id));

                                // deselect all and select only last added if not multiple
                                if (!additional.multiple) {
                                    $el.jstree(true).deselect_all();
                                    $el.jstree('select_node', pk(data.id));
                                }
                            }
                        }
                    );
                }
            };
            var observer = new MutationObserver(function(mutations) {
                mutations.forEach(name_handler);
            });
            var config = {childList: true, subtree: true};
            observer.observe($('#'+attr_name).get(0), config);

            // update from popup add/delete
            $('#'+attr_name).on('change', function(ev) {
                var current_options = [];
                $('#'+attr_name+' option').each(function() {current_options.push(this.value);});

                // handle deletes
                var diff = all_options.filter(function(el) {return current_options.indexOf(el) < 0;});
                for (var i=0; i<diff.length; ++i)
                    $el.jstree('delete_node', pk(diff[i]));

                // get active values
                var active = $(ev.target).val();
                if (typeof active === 'string') // for not multiple val() returns a string only
                    active = [active];
                if (!active)                    // for empty multiple val() returns null
                    active = [];

                // find missing values from active
                var missing = [];
                for (i = 0; i < active.length; ++i)
                    if (all_options.indexOf(active[i]) === -1)
                        missing.push(active[i]);

                // important: update options so we catch consecutive inserts/deletes
                all_options = current_options;

                // nothing to insert
                if (!missing.length)
                    return;

                // check if missing is already rendered in tree
                var tree_items = $el.jstree(true).get_json('#', { flat: true }).map(
                    function(el) { return el.id; }
                );
                var final_missing = [];
                for (i=0; i<missing.length; ++i) {
                    if (tree_items.indexOf(pk(missing[i])) === -1)
                        final_missing.push(missing[i]);
                }
                if (!final_missing.length)
                    return;

                // request final missing from server
                var data = {
                    appmodel: additional.appmodel,
                    ids: final_missing,
                    sort: (additional.sort.length) ? 1 : 0
                };
                $.getJSON(
                    additional.updateurl,
                    $.param(data, true),
                    function (resp) {

                        // since tree could have changed in between get nodes again
                        var tree_items = $el.jstree(true).get_json('#', { flat: true }).map(
                            function(el) { return el.id; }
                        );

                        for (var i=0; i < resp.length; ++i) {
                            var data = resp[i];

                            // check if parent node exists, add node if not
                            for (var j=0; j<data.parents.length; ++j) {
                                if (tree_items.indexOf(pk(data.parents[j].id)) === -1) {
                                    $el.jstree().create_node(
                                        pk(data.parents[j].parent),
                                        {
                                            id: pk(data.parents[j].id),
                                            text: data.parents[j].name,
                                            state: {selected: false},
                                            data: {sort: data.sort}
                                        },
                                        'last'
                                    );
                                }
                            }

                            // check if item is already in tree
                            if (tree_items.indexOf(pk(data.id)) !== -1)
                                continue;

                            // insert node into tree
                            $el.jstree().create_node(
                                pk(data.parent),
                                {
                                    id: pk(data.id),
                                    text: data.name,
                                    state: {selected: true},
                                    data: {sort: data.sort}
                                },
                                'last'
                            );
                            $el.jstree()._open_to(pk(data.id));

                            // deselect all and select only last added if not multiple
                            if (!additional.multiple) {
                                $el.jstree(true).deselect_all();
                                $el.jstree('select_node', pk(data.id));
                            }
                        }
                    }
                );
            });
        });
    });
})(window.jQuery);

if (window.reverse_jquery) {
    window.jQuery = null;
    delete window.jQuery;
}
