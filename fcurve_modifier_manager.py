bl_info = {
    "name": "F-Curve Modifier Manager",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "Graph Editor > Sidebar > Modifiers",
    "description": "Enhances the display and manipulation of F-Curve modifiers",
    "warning": "",
    "doc_url": "",
    "category": "Animation",
}

import bpy
from bpy.types import Panel, Operator
from bpy.props import StringProperty, BoolProperty


class GRAPH_PT_fcurve_modifier_manager(Panel):
    """Panel to manage F-Curve modifiers across multiple selected F-Curves"""
    bl_label = "F-Curve Modifier Manager"
    bl_idname = "GRAPH_PT_fcurve_modifier_manager"
    bl_space_type = 'GRAPH_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Modifiers'
    
    @classmethod
    def poll(cls, context):
        # Only show the panel when F-Curves are selected
        return context.selected_editable_fcurves is not None and len(context.selected_editable_fcurves) > 0
    
    def draw(self, context):
        layout = self.layout
        
        # Get all selected F-Curves
        fcurves = context.selected_editable_fcurves
        fcurve_count = len(fcurves)
        
        # Display information about selected F-Curves
        layout.label(text=f"{fcurve_count} F-Curve{'s' if fcurve_count > 1 else ''} selected")
        
        if fcurve_count == 1:
            # Single F-Curve selected - show all its modifiers
            fcurve = fcurves[0]
            self.draw_single_fcurve_modifiers(layout, fcurve)
        elif fcurve_count > 1:
            # Multiple F-Curves selected - show common modifiers
            self.draw_common_modifiers(layout, fcurves)
            
        # Add new modifier operator
        layout.operator("graph.fcurve_add_modifier_to_selected")
    
    def draw_single_fcurve_modifiers(self, layout, fcurve):
        """Display all modifiers for a single F-Curve"""
        if not fcurve.modifiers:
            layout.label(text="No modifiers on this F-Curve")
            return
            
        for mod in fcurve.modifiers:
            box = layout.box()
            row = box.row()
            row.label(text=mod.type)
            row.operator("graph.fcurve_remove_modifier", text="", icon='X').modifier_name = mod.name
            
            # Display modifier properties
            if mod.type == 'GENERATOR':
                self.draw_generator_modifier(box, mod)
            elif mod.type == 'ENVELOPE':
                self.draw_envelope_modifier(box, mod)
            elif mod.type == 'CYCLES':
                self.draw_cycles_modifier(box, mod)
            elif mod.type == 'NOISE':
                self.draw_noise_modifier(box, mod)
            elif mod.type == 'LIMITS':
                self.draw_limits_modifier(box, mod)
            elif mod.type == 'STEPPED':
                self.draw_stepped_modifier(box, mod)
            # Add more modifier types as needed
    
    def draw_common_modifiers(self, layout, fcurves):
        """Display modifiers common to all selected F-Curves"""
        # Get modifiers from the first F-Curve
        if not fcurves[0].modifiers:
            layout.label(text="No common modifiers")
            return
            
        # Find common modifiers by type
        modifier_types = {}
        
        # First, collect all modifiers from the first F-Curve
        for mod in fcurves[0].modifiers:
            modifier_types[mod.type] = [mod]
        
        # Then check each other F-Curve to see if it has modifiers of the same type
        for fcurve in fcurves[1:]:
            for mod_type in list(modifier_types.keys()):
                found = False
                for mod in fcurve.modifiers:
                    if mod.type == mod_type:
                        modifier_types[mod_type].append(mod)
                        found = True
                        break
                if not found:
                    # This F-Curve doesn't have a modifier of this type, so remove it from common types
                    del modifier_types[mod_type]
        
        # Display common modifiers
        if not modifier_types:
            layout.label(text="No common modifiers")
            return
        
        # For each common modifier type, show UI
        for mod_type, mods in modifier_types.items():
            if len(mods) == len(fcurves):  # Ensure all F-Curves have this modifier
                box = layout.box()
                row = box.row()
                row.label(text=f"Common: {mod_type}")
                row.operator("graph.fcurve_remove_common_modifier", text="", icon='X').modifier_type = mod_type
                
                # Create a special sub-layout that will update all modifiers
                synced_layout = SyncedModifierLayout(box, fcurves, mod_type)
                
                # Display common modifier properties
                if mod_type == 'GENERATOR':
                    self.draw_generator_modifier(synced_layout, mods[0], is_common=True)
                elif mod_type == 'ENVELOPE':
                    self.draw_envelope_modifier(synced_layout, mods[0], is_common=True)
                elif mod_type == 'CYCLES':
                    self.draw_cycles_modifier(synced_layout, mods[0], is_common=True)
                elif mod_type == 'NOISE':
                    self.draw_noise_modifier(synced_layout, mods[0], is_common=True)
                elif mod_type == 'LIMITS':
                    self.draw_limits_modifier(synced_layout, mods[0], is_common=True)
                elif mod_type == 'STEPPED':
                    self.draw_stepped_modifier(synced_layout, mods[0], is_common=True)
                # Add more modifier types as needed
    
    # Helper methods to draw different modifier types
    
    def draw_generator_modifier(self, layout, mod, is_common=False):
        """Display Generator modifier properties"""
        layout.prop(mod, "mode")
        if mod.mode == 'POLYNOMIAL':
            layout.prop(mod, "poly_order")
        layout.prop(mod, "use_additive")
        
        # For coefficients which is a collection, we need special handling
        if not is_common:
            layout.prop(mod, "coefficients")
        else:
            layout.label(text="Coefficients (edit in single mode)")
    
    def draw_envelope_modifier(self, layout, mod, is_common=False):
        """Display Envelope modifier properties"""
        layout.prop(mod, "reference_value")
        layout.prop(mod, "default_min")
        layout.prop(mod, "default_max")
        
        # Control points would typically be handled in a separate UI
        if is_common:
            layout.label(text="Control points (edit in single mode)")
        else:
            layout.label(text=f"{len(mod.control_points)} control points")
            # Add UI for control points here
    
    def draw_cycles_modifier(self, layout, mod, is_common=False):
        """Display Cycles modifier properties"""
        layout.prop(mod, "mode")
        layout.prop(mod, "cycles_before")
        layout.prop(mod, "cycles_after")
    
    def draw_noise_modifier(self, layout, mod, is_common=False):
        """Display Noise modifier properties"""
        layout.prop(mod, "blend_type")
        layout.prop(mod, "scale")
        layout.prop(mod, "strength")
        layout.prop(mod, "phase")
        layout.prop(mod, "depth")
    
    def draw_limits_modifier(self, layout, mod, is_common=False):
        """Display Limits modifier properties"""
        row = layout.row()
        row.prop(mod, "use_min_x")
        if mod.use_min_x:
            row.prop(mod, "min_x")
            
        row = layout.row()
        row.prop(mod, "use_max_x")
        if mod.use_max_x:
            row.prop(mod, "max_x")
            
        row = layout.row()
        row.prop(mod, "use_min_y")
        if mod.use_min_y:
            row.prop(mod, "min_y")
            
        row = layout.row()
        row.prop(mod, "use_max_y")
        if mod.use_max_y:
            row.prop(mod, "max_y")
    
    def draw_stepped_modifier(self, layout, mod, is_common=False):
        """Display Stepped modifier properties"""
        layout.prop(mod, "frame_step")
        layout.prop(mod, "frame_offset")
        layout.prop(mod, "use_frame_start")
        if mod.use_frame_start:
            layout.prop(mod, "frame_start")
        layout.prop(mod, "use_frame_end")
        if mod.use_frame_end:
            layout.prop(mod, "frame_end")


class GRAPH_OT_fcurve_add_modifier_to_selected(Operator):
    """Add a modifier to all selected F-Curves"""
    bl_idname = "graph.fcurve_add_modifier_to_selected"
    bl_label = "Add Modifier to Selected"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Properties to store selected modifier types
    generator_selected: BoolProperty(name="Generator", default=False)
    envelope_selected: BoolProperty(name="Envelope", default=False)
    cycles_selected: BoolProperty(name="Cycles", default=False)
    noise_selected: BoolProperty(name="Noise", default=False)
    limits_selected: BoolProperty(name="Limits", default=False)
    stepped_selected: BoolProperty(name="Stepped", default=False)
    
    def execute(self, context):
        fcurves = context.selected_editable_fcurves
        if not fcurves:
            self.report({'ERROR'}, "No F-Curves selected")
            return {'CANCELLED'}
        
        # Add the selected modifiers to each F-Curve
        modifiers_added = 0
        for fcurve in fcurves:
            if self.generator_selected:
                fcurve.modifiers.new('GENERATOR')
                modifiers_added += 1
            if self.envelope_selected:
                fcurve.modifiers.new('ENVELOPE')
                modifiers_added += 1
            if self.cycles_selected:
                fcurve.modifiers.new('CYCLES')
                modifiers_added += 1
            if self.noise_selected:
                fcurve.modifiers.new('NOISE')
                modifiers_added += 1
            if self.limits_selected:
                fcurve.modifiers.new('LIMITS')
                modifiers_added += 1
            if self.stepped_selected:
                fcurve.modifiers.new('STEPPED')
                modifiers_added += 1
        
        # Report success
        if modifiers_added > 0:
            self.report({'INFO'}, f"Added {modifiers_added} modifiers to {len(fcurves)} F-Curves")
        else:
            self.report({'INFO'}, "No modifiers were selected")
        
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Select Modifier Types:")
        
        # List all available modifier types with toggle buttons
        col = layout.column(align=True)
        col.prop(self, "generator_selected", toggle=True)
        col.prop(self, "envelope_selected", toggle=True)
        col.prop(self, "cycles_selected", toggle=True)
        col.prop(self, "noise_selected", toggle=True)
        col.prop(self, "limits_selected", toggle=True)
        col.prop(self, "stepped_selected", toggle=True)
        # Add more modifier types if needed
    
    def invoke(self, context, event):
        # Reset selection state
        self.generator_selected = False
        self.envelope_selected = False
        self.cycles_selected = False
        self.noise_selected = False
        self.limits_selected = False
        self.stepped_selected = False
        
        return context.window_manager.invoke_props_dialog(self, width=300)


# We don't need this class anymore as its functionality is now in GRAPH_OT_fcurve_add_modifier_to_selected


class GRAPH_OT_fcurve_remove_modifier(Operator):
    """Remove a modifier from a single F-Curve"""
    bl_idname = "graph.fcurve_remove_modifier"
    bl_label = "Remove F-Curve Modifier"
    bl_options = {'REGISTER', 'UNDO'}
    
    modifier_name: StringProperty(
        name="Modifier Name",
        description="Name of the modifier to remove",
        default=""
    )
    
    def execute(self, context):
        fcurve = context.active_editable_fcurve
        if not fcurve:
            self.report({'ERROR'}, "No active F-Curve")
            return {'CANCELLED'}
        
        for i, mod in enumerate(fcurve.modifiers):
            if mod.name == self.modifier_name:
                fcurve.modifiers.remove(mod)
                break
        
        return {'FINISHED'}


class GRAPH_OT_fcurve_remove_common_modifier(Operator):
    """Remove a common modifier from all selected F-Curves"""
    bl_idname = "graph.fcurve_remove_common_modifier"
    bl_label = "Remove Common F-Curve Modifier"
    bl_options = {'REGISTER', 'UNDO'}
    
    modifier_type: StringProperty(
        name="Modifier Type",
        description="Type of the modifier to remove",
        default=""
    )
    
    def execute(self, context):
        fcurves = context.selected_editable_fcurves
        if not fcurves:
            self.report({'ERROR'}, "No F-Curves selected")
            return {'CANCELLED'}
        
        # Remove the modifier from each F-Curve
        for fcurve in fcurves:
            for i, mod in enumerate(fcurve.modifiers):
                if mod.type == self.modifier_type:
                    fcurve.modifiers.remove(mod)
                    break
        
        return {'FINISHED'}


class SyncedModifierLayout:
    """A special layout wrapper that syncs changes to all F-Curves with the same modifier type"""
    def __init__(self, layout, fcurves, modifier_type):
        self.layout = layout
        self.fcurves = fcurves
        self.modifier_type = modifier_type
        self.prop_hooks = {}
    
    def prop(self, data, property, *args, **kwargs):
        """Override prop to sync changes to all modifiers"""
        # Create a unique ID for this property to avoid duplicating operators
        prop_id = f"{self.modifier_type}_{property}"
        
        # Get the current value
        current_value = getattr(data, property)
        
        # Create a row for the property
        row = self.layout.row()
        
        # Add the property to the UI, but make it use our custom operator
        if prop_id not in self.prop_hooks:
            # First time seeing this property, create the standard UI
            kwargs["text"] = kwargs.get("text", property)
            row.prop(data, property, *args, **kwargs)
            
            # Register this property for syncing
            self.prop_hooks[prop_id] = True
            
            # Add sync operator to context
            op = row.operator("graph.fcurve_sync_modifier_property", text="", icon='LINKED')
            op.modifier_type = self.modifier_type
            op.property_name = property
            op.property_value = str(current_value)  # Store as string, will be converted based on type
        else:
            # We've already processed this property type
            kwargs["text"] = kwargs.get("text", property)
            row.prop(data, property, *args, **kwargs)
    
    # Pass through other layout methods as-is
    def __getattr__(self, attr):
        if hasattr(self.layout, attr):
            return getattr(self.layout, attr)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{attr}'")


class GRAPH_OT_fcurve_sync_modifier_property(Operator):
    """Sync a modifier property value to all selected F-Curves"""
    bl_idname = "graph.fcurve_sync_modifier_property"
    bl_label = "Sync Modifier Property"
    bl_options = {'INTERNAL'}
    
    modifier_type: StringProperty(
        name="Modifier Type",
        description="Type of modifier to sync",
        default=""
    )
    
    property_name: StringProperty(
        name="Property Name",
        description="Name of property to sync",
        default=""
    )
    
    property_value: StringProperty(
        name="Property Value",
        description="Value to sync (as string)",
        default=""
    )
    
    def execute(self, context):
        fcurves = context.selected_editable_fcurves
        if not fcurves:
            return {'CANCELLED'}
        
        # Get source value from the active F-Curve's modifier
        active_fcurve = context.active_editable_fcurve
        
        # If no active F-Curve is set, use the first selected one as fallback
        if active_fcurve is None:
            active_fcurve = fcurves[0]
            
        source_value = None
        
        for mod in active_fcurve.modifiers:
            if mod.type == self.modifier_type:
                if hasattr(mod, self.property_name):
                    source_value = getattr(mod, self.property_name)
                    break
        
        if source_value is None:
            return {'CANCELLED'}
        
        # Apply to all selected F-Curves
        for fcurve in fcurves:
            for mod in fcurve.modifiers:
                if mod.type == self.modifier_type:
                    if hasattr(mod, self.property_name):
                        try:
                            # Convert value based on target property type
                            prop_type = type(getattr(mod, self.property_name))
                            if prop_type == bool:
                                setattr(mod, self.property_name, bool(source_value))
                            elif prop_type == int:
                                setattr(mod, self.property_name, int(source_value))
                            elif prop_type == float:
                                setattr(mod, self.property_name, float(source_value))
                            else:
                                setattr(mod, self.property_name, source_value)
                        except:
                            # If conversion fails, just set directly
                            setattr(mod, self.property_name, source_value)
        
        return {'FINISHED'}


# Register and unregister functions
classes = (
    GRAPH_PT_fcurve_modifier_manager,
    GRAPH_OT_fcurve_add_modifier_to_selected,
    GRAPH_OT_fcurve_remove_modifier,
    GRAPH_OT_fcurve_remove_common_modifier,
    GRAPH_OT_fcurve_sync_modifier_property,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()