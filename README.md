# Overte Avatar Blender Tool

## OVERVIEW

In this repository you will find the Source Code for the Blender Extension, and documentation on how to use the tool.

This tool allows the user to import an avatar into Overte (or derivatives) with greater speed than manually inputting all of the bone names and manually invoking "Recalculate Roll".

This tool does not rely on Pattern Matching, meaning even if your bones names are scrambled, so long as the heirarchy is roughly correct and you know what you want to rename bones to (for example, knowing the Chest bone is Spine2 and that Spine1 is optional), you will be able to rename, reroll, and reparent everything at what feels like lightspeed!

## INSTALLATION

> [!TIP]
> If you want to develop this extension, simply clone this repository and add the folder containing this file as a Local Repository to the Extensions page in Preferences, then enable the Add-on in the Add-ons page.

> [!NOTE]
> Once I start making proper releases of this extension, the below steps will not be required, and instead a separate document will be made describing the process of creating a release.

Firstly, you will need this extension in the zip format.

Specifically, the format described by [the Blender documentation](https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html#add-on-extension).

This can be done by cloning this repository and creating a zip archive of the files inside the `overte_avatar_blender_tool` folder (but not the folder itself, if memory serves me right).

Blender may have a tool to perform this action itself, but I have never needed to use it. If anybody has used it, please fork this repository, update this README file, and create a pull request!

Once you have acquired the zipped extension, you can install it by going into Blender's Preferences, then Get Extensions, then the small drop down menu in the top right of the preferences screen, then selecting "Install from Disk...", then activating the add-on in the Add-ons menu if it has not been automatically activated.

## USAGE

> [!NOTE]
> I will be creating a video tutorial on how to use this extension at some point, once I have rounded out all of the features I want to add to this extension. I will also be doing a "speedrun" of multiple avatars back-to-back, to showcase what you should do in certain edge cases.
> But until I have created those videos, I will do my best to document the usage here.

> [!TIP]
> If you are still struggling to import your avatar after reading through this guide, don't despair! The folk in the Overte Hub will be willing to give you pointers on what to do, as well as the folk in Overte's Discord and Matrix servers. If you still can't figure out what to do, reach out to me, `lexibigcheese`, and I'll do what I can to help! If that still fails, contact your local spiritual leader and/or exorcist, as you may be haunted.

This guide assumes you know the basics of Blender's UI.
If you do not know, it would serve you well to read [Blender's documentation](https://docs.blender.org/manual/en/latest), and may also serve you well to [download the documentation](https://docs.blender.org/manual/en/latest/blender_manual_html.zip) and use a static web server (such as running `python3 -m http.server` in the extracted documentation) so that you do not hammer Blender's servers with HTTP requests.

We will begin by preparing how things look on screen to make it clearer what you are doing.

First, select your avatar's armature in Object Mode.

You will want:
 - The armature's viewport display to be `Display as: Stick`, `Show: ☑️ Names`, `☑️ In Front`, and `Axes ☑️`.
 - The meshes associated with the armature to be children of the armature.
 - The materials of the meshes to be simple enough for the [GLTF exporter of Blender](https://docs.blender.org/manual/en/latest/addons/import_export/scene_gltf2.html).

And if you want to prepare your avatar specifically for a speedrun, make use of the `Pack Resources` operator.

Now, save your blend file as the "starting point" for this process (you may think of it as a backup), then use `Save As` to start saving changes to a new blend file.

Now, we move onto using the extension in accordance with [The Avatar Standards documentation](https://docs.overte.org/en/latest/create/avatars/avatar-standards.html).

Select the armature using Object Mode, then change to Edit Mode.

This extension adds three menu items to the Armature menu in the top left of the 3D viewport (known as `VIEW3D_MT_edit_armature`):
 
 1. Auto Rename
 1. Auto Rename and Reparent
 1. Auto Flow Bone

For each of the above mentioned operators, I recommend right clicking on each and using `Assign Shortcut...` to assign these operators to <kbd>5</kbd>, <kbd>6</kbd>, and <kbd>7</kbd> respectively. However, you may choose to assign these operators to whatever keys you desire.

> [!TIP]
> You can use the <kbd>N</kbd> key in the 3D View to open and close the side panel.
>
> In the "Item" tab of the side panel, you can find the Overte Avatar To-do list, which will give you any errors, and tell you what bones you need to press <kbd>5</kbd> or <kbd>6</kbd> on
>
> Note that this list may be incomplete or inaccurate

We will now begin using the `Auto Rename` and `Auto Rename and Reparent` operators, which are the same operator, assume "the operator" is referring to the `Auto Rename` operator.

 1. Select the `Hips` bone of your avatar and Invoke.
 1. Select the `Spine` bone of your avatar and Invoke, which should bring up a menu where you can select `Spine`
 1. Assuming the active bone shifts to the next bone, Invoke and select `Spine2` if the bone is the Chest bone, or `Spine1` if it is between the Spine and Chest bones, Then Invoke on the Chest bone to rename it to `Spine2`.
 1. Select the Left Shoulder Bone and Invoke, then select `LeftShoulder`, and keep Invoking down the arm until you have renamed the `LeftHand` bone.
 1. For each finger on the hand, select the start of the finger, use Invoke to specify which finger you are renaming it to, then Invoke down the length of the finger, and repeat for all fingers on that hand.
 1. Repeat the steps taken for the Left Shoulder on the Right Shoulder.
 1. Invoke the operator on the Neck and Head bones,
 1. Invoke the operator on the Left Eye and Right Eye bones,
 1. Invoke the operator on the Left Leg and its children, then the Right Leg and its children.

> [!TIP]
> If you find a bone that does not rename, even if you think it should, try using the `Auto Rename and Reparent` version of the operator. You may need to guess when to use the reparent mode.

You should now have all of the bones renamed (and rerolled) to their correct values.

> [!TIP]
> Remember to save your progress, and even better, use `Save As`!

> [!TIP]
> You may also test your avatar at this stage by performing the exporting step early, then using a `file://` url to reference avatar. Note that using the `file://` method of referring to your avatar means that only you will be able to see your avatar.

Now, we can start making use of the `Auto Flow Bone` operator.

Usage of this operator is simple:

 1. Select the start of a chain of bones that you would like to be "jiggly"
 1. Invoke the `Auto Flow Bone` operator and input the name you would like to assign to this chain of bones. Pressing Enter twice should now execute the operator.
 1. The operator will now start naming the chain of bones with the convention `flow_name_index` with indices starting from 1, and will stop after it has renamed a bone with a number of children that is not equal to one (so either a "dead end" or a "fork in the road")

> [!NOTE]
> To use these flow bones, use the `Flow` app in Overte with your avatar equipped. More on this later.

Now, we need to rename some of your avatar's meshes' shape keys (aka blendshapes).

There are three important blendshapes you will want on your avatar for it to be expressive:

 1. `JawOpen`
 1. `EyeBlink_L`
 1. `EyeBlink_R`

If your avatar does not have an obviously named "Open Jaw" shape key, you should direct your attention to any shape keys named "aa", as that shape key can be renamed to `JawOpen`

> [!NOTE]
> At the time of writing, Overte does not use viseme blendshapes, but it likely will in the future, so if you DO rename your "aa" viseme to `JawOpen`, make a note of what it was originally named so that you may rename it back to the original name.
> If you make sure to keep multiple versions of your blend file at different stages in the process, it will come in handy for when these changes occur.

> [!NOTE]
> If your avatar does not have separate "Eye Blink" shape keys, there is  [a method](https://www.reddit.com/r/blenderhelp/comments/v6vsz3/comment/ibhqi03/) to split it into left and right hand shape keys.
> I may, in the future, either add an operator to this extension, or make another extension, to perform this method in a slightly more user friendly way. There may also already be an extension that performs this task, and if you, the reader, know of an extension, then please fork this repository, update this README, and create a pull request!

For more information about the blendshapes that Overte supports, check [the relevant documentation](https://docs.overte.org/en/latest/create/avatars/avatar-standards.html#blendshapes)

> [!TIP]
> Remember to save your progress!

Now, you can export your avatar as `.glb`. You may want to limit the exported items to only visible items.

You can test your avatar using `file://` urls, which will only be visible locally (only to you and nobody else).

From here, you can upload your avatar to somewhere like [Catbox](https://catbox.moe/), [Litterbox](https://litterbox.catbox.moe) for temporary uploads, or anywhere that lets you create a direct HTTP download for your avatar, and start using it in Overte!

To add more information to your avatar, such as the parameters for the physics the Flow app applies to yoru avatar, and giving your avatar a proper thumbnail, check out [The Avatar Standards documentation](https://docs.overte.org/en/latest/create/avatars/avatar-standards.html), and the other surrounding documentation for usage of `.fst` files.

Now then, have fun porting your avatar/avatars to Overte!

If you want to have even more fun, record yourself doing a speedrun of porting your avatar into Overte, starting from the step where you had configured your materials, the viewport display of the armature, and your keybinds.

That's all from me for now, good luck!

## VERSION 1.2 ADDITIONS

A few new operators and small improvements since the previous write up. They are listed roughly in the order you will run into them while porting an avatar.

### Hotkeys

The operators `Auto Rename`, `Auto Rename and Reparent`, and `Auto Flow Bone` are now bound to <kbd>5</kbd>, <kbd>6</kbd>, and <kbd>7</kbd> on enable, so you no longer need to right click each one and use `Assign Shortcut...` by hand. You may still rebind them to whatever you like.

> [!NOTE]
> If you previously bound these operators to your own keys, those bindings will still be there alongside the new ones. Go to `Edit > Preferences > Keymap` and remove the duplicates if you want a clean setup.

### Per Bone Descriptions

When `Auto Rename` (or its reparent variant) pops up the search menu, each entry now shows a short description of what that bone is, such as "Chest (upper spine)" or "Left thumb, base joint". This should make it easier to pick the right name when more than one is available, especially around the fingers.

### Smarter Active Bone Advancement

After Invoking `Auto Rename`, the active bone now tries to advance to the bone you are most likely to rename next, rather than always stopping at the first child. If there is exactly one child whose name is not already a known rule (so a child you have not renamed yet), the active bone hops to it. When you reach a "dead end" such as `LeftHand` after all of its fingers have been renamed, the active bone hops back to the start of that chain (such as `Spine2`), so you can carry straight on with the other side without having to navigate back manually.

### Recalculate All Rolls

A new operator, available as a button at the top of the `Overte Avatar To-Do List` panel and also in the Armature menu in Edit Mode. Invoking it walks the rules and recalculates the roll on every bone whose name matches one of the standard avatar bones (Hips, Spine, LeftArm, and so on).

This is mostly useful as a safety net, for example after importing an avatar that came in with strange rolls, or if you just want to be sure nothing was missed while renaming.

### Split Shape Key by Axis

If your avatar came with a single "Eye Blink" shape key, this operator splits it into `Eye BlinkLeft` and `Eye BlinkRight` along the X axis, so you no longer need to follow the Reddit method linked further up in this README. It also works on any other symmetrical shape key you would like to split, not just eye blinks.

To use it:
 0. Select the mesh that owns the shape key, in Object Mode.
 0. In the Properties editor, switch to the Object Data Properties tab (the green triangle icon).
 0. Open the Shape Keys section, click the small dropdown menu next to the shape key list, and select `Split by Axis (Overte)`.
 0. The source shape key name defaults to "Eye Blink". Change it if your key is named something else, and pick names for the left and right halves if you do not want the default `<source>Left` and `<source>Right` pair.

> [!TIP]
> The operator assumes Blender's standard convention that +X is the character's left side. If your avatar ends up blinking on the wrong sides, the easiest fix is to swap the left and right names in the dialog and Invoke again.

### Treat Toes As Required

A new preference under `Edit > Preferences > Add-ons > Overte Avatar Blender Tool > Preferences`. Off by default. When on, `LeftToeBase`, `LeftToe_End`, `RightToeBase`, and `RightToe_End` will show up as Required entries in the To-Do list instead of Optional, which is handy if you are working on a stylised avatar where the toes are always part of the rig.

### Flow Chain Validation

The To-Do List panel now flags `flow_*_N` chains that have gone wrong. The most common cause is reparenting one of the middle links by accident, which the panel will now tell you about so you can fix it before exporting.

## CONTRIBUTION POLICY

This repository does not accept AI generated documentation, code, or other content in pull requests.
