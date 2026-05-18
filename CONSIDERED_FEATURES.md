# Considered Features of the Overte Avatar Blender Tool

This document outlines feature requests I have received, considered, or would like to implement, the pros and cons of implementing such features, and the technical difficulties of implementing such features.

This document may be considered a subset of a "FAQ" (Frequently Asked Questions) document, but also considered as a "To-do" list of features (and a "To-do-for-someone-other-than-me" in the case of some features).

## Material setup dialogs / panels

Many users of this extension likely do not know how to use the Shader Editor view, and even when they do, they do not know the quirks of the GLTF exporter, nor the quirks of rendering in Overte.

I, too, do not know all of the quirks of Avatar setup and Material setup in Overte, but I have been made aware of the existance of such quirks by other players of Overte.

Therefore, instead of requiring the user to search for guides on how to set up materials for situations such as:

 - Combining height and normal maps
 - What to do with emission
 - How to make the glass of eyes look good

And any other such cases, I would like to turn any such guides created into "Wizards", where the documentation appears as you are using the extension.

Then, when a user asks "How do I set up my material in such and such way", a user who knows the features of this extension can point at the relevant operator / panel / wizard / documentation, and an inquisitive user may find the answers to their questions much faster.

These material setup helpers should also allow the user to set up an MToon material (this will require FST editing/exporting features in the extension too), and with even more work will eventually allow the user to set up Custom Shaders!

I can see numerous ways to implement such features, yet I do not have enough knowledge about Material Setup to make a call on how they should be implemented.

So far, I have made these considerations:

 - The implementation should be generic over the PBR, MToon, and any Custom Shaders that the user, avatar creator, or shader developers want to include
 - The implementation should attempt to preview (or enable previewing) how the material renders in the 3D view, likely requiring use of the `gpu` module
 - The implementation should allow wizards to be added with "Wizard Packs", and these wizards should be included in the `.blend` file, likely through use of Text resources, running them as scripts, and modifying some attr on the `bpy` module.

Note that should a solution be made to only solve a static amount of problems, it would be best to have that be its own extension, and to use `bpy.types.WindowManager.invoke_props_dialog`, which is something I have considered creating as a stop-gap (because I am aware that these problems do need solving one way or another for the time being, even if it is not the perfect solution).

## Custom Shader Node Graph / Shader Nodes to GLSL

This would be awesome, and could probably be done by making a subclass of `bpy.types.NodeTree` or by adapting and extending `bpy.types.ShaderNodeTree`'s functionality.

I reckon it wouldn't be hard to create a proof of concept for this, but I forsee this devolving into spaghetti code, so however this ends up getting implemented will likely need to make use of decorated functions and/or classes, a flexible way of traversing the node tree, and knowledge of how to generate and optimise GLSL code.


## Virtual Renaming of Bones / Using the FST file to rename bones / Having a UI to select all bones before renaming all bones

> [!NOTE]
> Tl;Dr: Check the To-Do list, found in the Items menu of the Sidebar (N-Menu) of the 3D view, which seeks to do the job of such a feature. The main hurdles are the rendering of Virtual Renames, the bugs introduced by increased code complexity, and the fact that you often end up having to modify the armature anyway, specifically in the cases of the Eyes, the Feet, and the Legs in the case of Digitigrade legs.
>
> And considering how fast you can rename all of your bones without such a UI, it does not feel worth implementing. However, if you can implement such a feature and work around all issues with grace, I will happily accept a pull request!

I have been asked in the past a question with multiple variants, which starts with:

> Why not have a panel where you can select a bone for each bone the armature needs?

Followed by either:

 - > Then a button to rename all the bones at once based off that information
 - > Then a button to export that information in the FST file

In either such case, I will call this feature "Virtual Renaming"

Personally, I think Virtual Renaming WOULD be a good feature to have, with BOTH the option to either rename all your bones simultaneously OR export that information in an FST file.

In fact, such a feature would greatly improve the flexibility of my extension.

However, there is a fairly large hurdle in implementing this feature...

When you are renaming all of your bones during normal use of my extension, you will have bone names displayed in your viewport.

This Virtual Renaming feature would need its own way to render bone names to support the already existing workflow.

Also, a User Interface in which you select each bone you want to rename is very tedious to use, much slower than just spamming the <kbd>5</kbd> (or <kbd>6</kbd>) key.

And with how much code complexity this would add to the logic for renaming bones, numerous bugs will likely be introduced.

This is why I have the "To-do" list panel in the Items section of the Sidebar of the 3D View, so that you know which bones you need to (or can) rename next.

Additionally, while you are renaming bones, my extension is running callbacks on some of the bones (Currently just the Eyes, but I am considering a callback for the Feet) which modify the bone data in a way that would either:

 - All have to be handled simultaneously by the user or
 - Not be possible to do with an FST
 
As these callbacks (can) modify the positions (head/tail) of the bones, which the user should be present for.
