'''
ListAdapter
===========

.. versionadded:: 1.4

Notes:

    - Consider adding the functionality for locking changes to the associated
      data -- whether or not editing of item_view_instances is allowed.
      This could be controlled simply with an is_editable boolean, but would
      involve more work in the implementation, of course.
'''

from kivy.properties import ListProperty, DictProperty, ObjectProperty
from kivy.lang import Builder
from kivy.adapters.adapter import Adapter
from kivy.adapters.mixins.selection import SelectionSupport


class ListAdapter(SelectionSupport, Adapter):
    '''ListAdapter is an adapter around a simple Python list.

    From the SelectionSupport mixin, ListAdapter has these properties:

        - selection
        - selection_mode
        - allow_empty_selection

    and several methods used in selection operations.

    From Adapter, ListAdapter gets these properties:

        - cls, for the list item class to use to instantiate row view
               instances
        - template, an optional kv template to use instead of a python class
                    (to use instead of cls)
        - args_converter, an optional function to transform data item argument
                          sets, in preparation for either a cls instantiation,
                          or a kv template invocation
    '''

    data = ListProperty([])
    '''The data list property contains a list of objects that will be used
    directly if no args_converter function is provided. If there is an
    args_converter, the data objects will be passed to it, for instantiation
    of item view class (cls) instances.
    '''

    def __init__(self, data, **kwargs):
        if type(data) not in (tuple, list):
            raise Exception('ListAdapter: input must be a tuple or list')
        super(ListAdapter, self).__init__(**kwargs)

        # Reset and update selection, in SelectionSupport, if data changes.
        self.bind(data=self.initialize_selection)

        # Do the initial set -- triggers check_for_empty_selection().
        self.data = data

    def get_count(self):
        return len(self.data)

    def get_item(self, index):
        if index < 0 or index >= len(self.data):
            return None
        return self.data[index]

    def get_view(self, index):
        '''This method is identical to the one in Adapter, but here we pass
        self to the list item class (cls) instantiation, so that the list
        item class, required to mix in SelectableItem, will have access to
        ListAdapter for calling to SelectionSupport methods.
        '''
        item = self.get_item(index)
        if item is None:
            return None

        item_args = None
        if self.args_converter:
            item_args = self.args_converter(item)
        else:
            item_args = item

        item_args['list_adapter'] = self

        if self.cls:
            print 'CREATE VIEW FOR', index
            instance = self.cls(**item_args)
            return instance
        else:
            return Builder.template(self.template, **item_args)

    def on_selection_change(self, *args):
        pass


class SelectableListsAdapter(ListAdapter):
    '''SelectableListsAdapter is specialized for use in chaining
    list_adapters in a "cascade," where selection of the first,
    changes the selection of the next, and so on.
    '''

    selectable_lists_dict = DictProperty({})
    '''The selection of the observed_list_adapter, which must be single
    selection here, is the key into selectable_lists_dict, which is a dict
    of list item lists.
    '''

    observed_list_adapter = ObjectProperty(None)

    selectable_lists_dict = DictProperty({})

    def __init__(self, **kwargs):
        super(SelectableListsAdapter, self).__init__(**kwargs)
        self.observed_list_adapter.bind(
                on_selection_change=self.on_selection_change)

    def on_selection_change(self, *args):
        observed_selection = self.observed_list_adapter.selection

        if len(observed_selection) == 0:
            self.data = []
            return

        self.data = self.selectable_lists_dict[str(observed_selection[0])]


class AccumulatingListAdapter(ListAdapter):
    '''AccumulatingListAdapter is a list adapter whose
    data is formed by the selection of an observed list adapter.

    Selection will accumulate as either single or multiple selection
    events happen.
    '''

    observed_list_adapter = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(AccumulatingListAdapter, self).__init__(**kwargs)
        self.observed_list_adapter.bind(
                on_selection_change=self.on_selection_change)

    def on_selection_change(self, *args):
        observed_selection = self.observed_list_adapter.selection

        if len(observed_selection) == 0:
            self.data = []
            return

        self.data = [str(obj.text) for obj in observed_selection]
