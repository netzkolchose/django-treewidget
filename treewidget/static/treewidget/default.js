(function($) {
    $(document).ready(function() {
        $('.klaus').each(function(idx, el) {
            var $el = $(el);
            var data = $('#' + el.id + ' + input').val();
            $el.jstree({'core': {'data': JSON.parse(data), "check_callback" : true}, 'plugins': ['dnd', 'contextmenu']});
        });
    });

    $(document).on('move_error.treewidget', function() {
        alert('Error while moving node!');
    });

    function jstree_init(id, settings) {
        var el = $('#treewidget_' + id);

        $('#treewidget-container_' + id + ' a.expand').on('click',
            function(){
                el.jstree('open_all');
            });
        $('#treewidget-container_' + id + ' a.collapse').on('click',
            function(){
                el.jstree('close_all');
            });
        $('#treewidget-container_' + id + ' a.selected').on('click',
            function(){
                el.jstree('close_all');
                var selected = el.jstree('get_selected', true);
                for (var i=0; i<selected.length; ++i)
                    el.jstree()._open_to(selected[i].id);
            });

        return el
            .on('select_node.jstree', function(e, data){
                var selected = $('#treewidget_' + id).jstree('get_selected');
                // clear 'em all
                $('#' + id + ' option').each(function(idx, el) {
                    el.selected = false;
                });
                // set selected
                selected.forEach(function(el) {
                    $('#' + id + ' option[value="' + el.split('_').pop() + '"]')[0].selected = true;
                });
                $('#' + id).change();
            })
            .on('deselect_node.jstree', function(e, data){
                $('#' + id + ' option[value="' + data.node.id.split('_').pop() + '"]')[0].selected = false;
                $('#' + id).change();
            })
            .jstree(settings);
    }

    $(document).ready(function() {
        $('.treewidget').each(function(idx, el) {
            var $el = $(el);
            var settings = $el.data('treewidget-settings');
            var _id = $el.data('id');
            var multiple = $el.data('multiple');
            var appmodel = $el.data('appmodel');
            var search = $el.data('search');
            var updateurl = $el.data('updateurl');
            var dnd = $el.data('dnd');
            var moveurl = $el.data('moveurl');
            var sort = $el.data('sort');

            // add plugins as needed
            var plugins = settings.plugins || [];
            settings.plugins = plugins;

            // add search plugin
            if (search && plugins.indexOf('search') === -1)
                plugins.push('search');

            // sort plugin
            if (sort.length) {
                if (plugins.indexOf('sort') === -1)
                    plugins.push('sort');
                settings.sort = function(a, b) {
                    var data_a = this.get_node(a).data.sort;
                    var data_b = this.get_node(b).data.sort;
                    for (var i=0; i<sort.length; ++i) {
                        if (data_a[i] === data_b[i])
                            continue;
                        return ((data_a[i] > data_b[i]) ? 1 : -1) * sort[i];
                    }
                    return (a1.text > b1.text) ? 1 : -1;
                };
            }

            // drag' drop plugin
            if (dnd) {
                plugins.push('dnd');
            } else {
                var index = plugins.indexOf('dnd');
                if (index !== -1)
                    plugins.splice(index, 1);
            }

            // init jstree
            var obj = jstree_init(_id, settings);
            $(obj).jstree().settings.core.multiple = multiple;


            // drag'n drop handler
            if (dnd) {
                var move_node_handler = function (ev, data) {
                    var parent_node = $(obj).jstree('get_node', data.parent);
                    var position = parent_node.children.indexOf(data.node.id);
                    var prev = null;
                    if (position > 0)
                        prev = parent_node.children[position - 1].split('_').slice(-1)[0];
                    var next = null;
                    if (position + 1 < parent_node.children.length)
                        next = parent_node.children[position + 1].split('_').slice(-1)[0];
                    $.getJSON(
                        moveurl,
                        $.param({
                            appmodel: appmodel,
                            id: data.node.id.split('_').slice(-1)[0],
                            parent: (data.parent === '#') ? null : data.parent.split('_').slice(-1)[0],
                            prev: prev,
                            next: next
                        }, true),
                        function (resp) {
                            if (resp)
                                return;
                            // revert to last state and throw alert box
                            $(obj).off('move_node.jstree', move_node_handler);
                            $(obj).jstree('move_node', data.node, data.old_parent, data.old_position);
                            $('#'+data.node.id).trigger('move_error.treewidget', [data]);
                            $(obj).on('move_node.jstree', move_node_handler);
                        }
                    );
                };
                $(obj).on('move_node.jstree', move_node_handler);
            }

            // search callback
            if (search) {
                $(function () {
                    var to = false;
                    $('#treewidget-search_' + _id).keyup(function () {
                        if (to) clearTimeout(to);
                        to = setTimeout(function () {
                            var v = $('#treewidget-search_' + _id).val();
                            $(obj).jstree(true).search(v);
                        }, 250);
                    });
                });
            }

            // widget is disabled
            if ($el.data('disabled')) {
                $el.addClass('treewidget-disabled');
                $($(obj).jstree(true).get_json('#', { flat: true })).each(function() {
                    $(obj).jstree("disable_node", this.id);
                });
            }

            // exit here if we cant update elements
            if (!updateurl)
                return;

            // get all known options
            var all_options = [];
            $('#'+_id+' option').each(function() {all_options.push(this.value);});
            var all_texts = {};
            $('#'+_id+' option').each(function() {
                $(this).text('#' + $(this).text());
                all_texts[this.value] = $(this).text();
            });

            // listener for name or position changes
            $('#'+_id).on('DOMSubtreeModified', function(ev) {
                if (ev.target !== $('#'+_id)[0]) {
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

                    var tree_items = $(obj).jstree(true).get_json('#', { flat: true }).map(
                        function(el) { return el.id; }
                    );

                    // most like an entry got edited: renamed or moved in tree - update needed
                    // FIXME: handle children of a moved node
                    $.getJSON(
                        updateurl,
                        $.param({
                            appmodel: appmodel,
                            ids: [ev.target.value],
                            sort: (sort.length) ? 1 : 0
                        }, true),
                        function (resp) {
                            for (var i=0; i < resp.length; ++i) {
                                var data = resp[i];

                                // first check if node has still same parent to skip parent inserts
                                var old_node = $(obj).jstree(true).get_node('treewidget_' + _id + '_' + data.id);
                                if (old_node) {
                                    if ('treewidget_' + _id + '_' + data.parent === old_node.parent) {
                                        // parent is still the same, change text only
                                        $(obj).jstree('rename_node', old_node, data.name);
                                        continue;
                                    }
                                }
                                // must delete old node first
                                $(obj).jstree('delete_node', 'treewidget_' + _id + '_' + data.id);

                                // check if parent node exists, add node if not
                                for (var j=0; j<data.parents.length; ++j) {
                                    if (tree_items.indexOf('treewidget_' + _id + '_' + data.parents[j].id) === -1) {
                                        $(obj).jstree().create_node(
                                            (data.parents[j].parent) ? 'treewidget_' + _id + '_' + data.parents[j].parent : null,
                                            {
                                                id: 'treewidget_' + _id + '_' + data.parents[j].id,
                                                text: data.parents[j].name,
                                                state: {selected: false},
                                                data: {sort: data.sort}
                                            },
                                            'last'
                                        );
                                    }
                                }

                                // insert node into tree
                                $(obj).jstree().create_node(
                                    (data.parent) ? 'treewidget_' + _id + '_' + data.parent : null,
                                    {
                                        id: 'treewidget_' + _id + '_' + data.id,
                                        text: data.name,
                                        state: {selected: true},
                                        data: {sort: data.sort}
                                    },
                                    'last'
                                );
                                $(obj).jstree()._open_to('treewidget_' + _id + '_' + data.id);

                                // deselect all and select only last added if not multiple
                                if (! $(obj).jstree().settings.core.multiple) {
                                    $(obj).jstree(true).deselect_all();
                                    $(obj).jstree('select_node', 'treewidget_' + _id + '_' + data.id);
                                }
                            }
                        }
                    );
                }
            });

            // update from popup changes
            $('#'+_id).on('change', function(ev) {
                var current_options = [];
                $('#'+_id+' option').each(function() {current_options.push(this.value);});

                // handle deletes
                var diff = all_options.filter(function(el) {return current_options.indexOf(el) < 0;});
                for (var i=0; i<diff.length; ++i)
                    $(obj).jstree('delete_node', 'treewidget_' + _id + '_' + diff[i]);

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
                var tree_items = $(obj).jstree(true).get_json('#', { flat: true }).map(
                    function(el) { return el.id; }
                );
                var final_missing = [];
                for (i=0; i<missing.length; ++i) {
                    if (tree_items.indexOf('jstreewidget_' + _id + '_' + missing[i]) === -1)
                        final_missing.push(missing[i]);
                }
                if (!final_missing.length)
                    return;

                // request final missing from server
                var data = {
                    appmodel: appmodel,
                    ids: final_missing,
                    sort: (sort.length) ? 1 : 0
                };
                $.getJSON(
                    updateurl,
                    $.param(data, true),
                    function (resp) {
                        for (var i=0; i < resp.length; ++i) {
                            var data = resp[i];

                            // check if parent node exists, add node if not
                            for (var j=0; j<data.parents.length; ++j) {
                                if (tree_items.indexOf('treewidget_' + _id + '_' + data.parents[j].id) === -1) {
                                    $(obj).jstree().create_node(
                                        (data.parents[j].parent) ? 'treewidget_' + _id + '_' + data.parents[j].parent : null,
                                        {
                                            id: 'treewidget_' + _id + '_' + data.parents[j].id,
                                            text: data.parents[j].name,
                                            state: {selected: false},
                                            data: {sort: data.sort}
                                        },
                                        'last'
                                    );
                                }
                            }

                            // insert node into tree
                            $(obj).jstree().create_node(
                                (data.parent) ? 'treewidget_' + _id + '_' + data.parent : null,
                                {
                                    id: 'treewidget_' + _id + '_' + data.id,
                                    text: data.name,
                                    state: {selected: true},
                                    data: {sort: data.sort}
                                },
                                'last'
                            );
                            $(obj).jstree()._open_to('treewidget_' + _id + '_' + data.id);

                            // deselect all and select only last added if not multiple
                            if (! $(obj).jstree().settings.core.multiple) {
                                $(obj).jstree(true).deselect_all();
                                $(obj).jstree('select_node', 'treewidget_' + _id + '_' + data.id);
                            }
                        }
                    }
                );
            });
        });

        // process all hide links
        $('.treewidget_hide_link').each(function(idx, el) {
            var $el = $(el);
            var $field = $el.parent().parent().parent();
            var $orig_label = $field.find(' > div > label');
            $field.prepend('<label class="treewidget_hide_label ' + $orig_label.attr('class') + '" for="' + $el.data('hide') + '"><a href="javascript:void(0)">' + $orig_label.text() + '</a></label>');
            $orig_label.hide();
            if ($el.data('data') === 'False')
                $field.children('div').hide();
        });
        $('.treewidget_hide_label').each(function(idx, el) {
            var $el = $(el);
            $el.on('click', function (ev) {
                $target = $(ev.currentTarget).next();
                if ($target.is(":visible"))
                    $target.hide();
                else
                    $target.show();
            });
        });
    });
})(window.jQuery);

if (window.reverse_jquery) {
    window.jQuery = null;
    delete window.jQuery;
}
