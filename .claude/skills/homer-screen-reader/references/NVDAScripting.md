---
title: "Writing add-ons and plugins for NVDA"
lang: en
---

# Writing add-ons and plugins for NVDA

This guide holds two documents from two publishers, gathered on 31 August 2026: NV Access's own NVDA Developer Guide, and the NVDA Add-on Development Guide written by the community add-on team.

The developer guide covers app modules, global plugins, the add-on API and its policy, translation, and the internals a plugin may use. The add-on team's guide covers what it takes to build, package and publish an add-on, and is the longer of the two. Read together they answer both halves of the question: what NVDA lets a plugin do, and how to ship one.

This guide is an exception to the rule this collection otherwise keeps, and the same exception as JAWSScripting: everything else here is written for someone using a program, and this is written for someone extending one. It is included because scripting a screen reader is how a blind user makes an inaccessible program usable, which is closer to self-defence than to software engineering.

## Contents

- The add-on development guide: Add-on Basics
    - [Installing NVDA Add-ons](#installing-nvda-add-ons)
    - [What Are Add-on Modules?](#what-are-add-on-modules)
    - [What Are Add-on Packages?](#what-are-add-on-packages)
    - [What are Add-ons?](#what-are-add-ons)
- The add-on development guide: Add-on module components and development tips
    - [Add-on module components and development tips](#add-on-module-components-and-development-tips)
    - [Add-on planning and development tips](#add-on-planning-and-development-tips)
    - [Do's and don'ts](#dos-and-donts)
    - [Events (The add-on development guide: Add-on module components and development tips)](#events-the-add-on-development-guide-add-on-module-components-and-development-tips)
    - [Events within objects](#events-within-objects)
    - [Examining object hierarchy](#examining-object-hierarchy)
    - [Example 1: Finding the value of a slider in a program](#example-1-finding-the-value-of-a-slider-in-a-program)
    - [Example 2: A basic script dictionary and message output](#example-2-a-basic-script-dictionary-and-message-output)
    - [Example 3: script information using script decorator](#example-3-script-information-using-script-decorator)
    - [Example 4: Scripts for specific objects](#example-4-scripts-for-specific-objects)
    - [Example 5: Announcing the changed name of a control](#example-5-announcing-the-changed-name-of-a-control)
    - [Examples of overlay classes and modified roles](#examples-of-overlay-classes-and-modified-roles)
    - [A few other remarks on scripts](#a-few-other-remarks-on-scripts)
    - [Focus vs. navigator object](#focus-vs-navigator-object)
    - [Frequently Asked Questions about add-on components and development](#frequently-asked-questions-about-add-on-components-and-development)
    - [Input and output: scripts and UI messages](#input-and-output-scripts-and-ui-messages)
    - [Let's build an add-on](#lets-build-an-add-on)
    - [List of possible events](#list-of-possible-events)
    - [Other components](#other-components)
    - [Other useful object-related goodies](#other-useful-object-related-goodies)
    - [The Python Console](#the-python-console)
    - [Script lookup order and command conflicts](#script-lookup-order-and-command-conflicts)
    - [Specialist objects and overriding object properties at runtime](#specialist-objects-and-overriding-object-properties-at-runtime)
    - [Working with objects on screen](#working-with-objects-on-screen)
- The add-on development guide: Advanced Code Examples and Features
    - [Advanced Code Examples and Features](#advanced-code-examples-and-features)
    - [Defining add-on specific command-line options](#defining-add-on-specific-command-line-options)
    - [Interactive Dialogs](#interactive-dialogs)
    - [Settings Dialogs And Panels](#settings-dialogs-and-panels)
    - [Threading](#threading)
    - [Using external Python modules](#using-external-python-modules)
    - [Using The Log](#using-the-log)
- The add-on development guide: Appendices
    - [Appendix A: add-on terms dictionary](#appendix-a-add-on-terms-dictionary)
    - [Appendix B: Programming and Python concepts every add-on developer needs to know](#appendix-b-programming-and-python-concepts-every-add-on-developer-needs-to-know)
    - [Appendix C: Add-on type comparison](#appendix-c-add-on-type-comparison)
    - [Appendix D: notes and references for scripters of other screen readers](#appendix-d-notes-and-references-for-scripters-of-other-screen-readers)
- The add-on development guide: Audience
    - [Add-on distribution process for NV Access add-on Store](#add-on-distribution-process-for-nv-access-add-on-store)
    - [Audience](#audience)
    - [A special note about Windows Store version of NVDA](#a-special-note-about-windows-store-version-of-nvda)
    - [A special note for scripters of other screen readers](#a-special-note-for-scripters-of-other-screen-readers)
    - [Special note on 64-bit NVDA](#special-note-on-64-bit-nvda)
    - [Special note on NVDA backward compatibility](#special-note-on-nvda-backward-compatibility)
    - [Special note on Python version](#special-note-on-python-version)
    - [A very important note about control types module changes in NVDA 2021.2](#a-very-important-note-about-control-types-module-changes-in-nvda-20212)
    - [A very important note about migrating custom extension code to development scratchpad](#a-very-important-note-about-migrating-custom-extension-code-to-development-scratchpad)
- The add-on development guide: Drivers
    - [Driver components](#driver-components)
    - [Drivers](#drivers)
    - [A Few important things to remember before, during and after driver development](#a-few-important-things-to-remember-before-during-and-after-driver-development)
    - [Typical driver development steps](#typical-driver-development-steps)
- The add-on development guide: Enhancers
    - [Enhancer components](#enhancer-components)
    - [Enhancers](#enhancers)
    - [A Few important things to remember before, during and after enhancer development](#a-few-important-things-to-remember-before-during-and-after-enhancer-development)
    - [Typical enhancer development steps](#typical-enhancer-development-steps)
- The add-on development guide: Getting started: Hands-on examples
    - [Example 1 code explanation](#example-1-code-explanation)
    - [Example 1: Hear a tone when pressing NVDA+A](#example-1-hear-a-tone-when-pressing-nvdaa)
    - [Example 2 code explanation](#example-2-code-explanation)
    - [Example 2: Generate a tone when switching to Notepad](#example-2-generate-a-tone-when-switching-to-notepad)
    - [A few tips for beginners](#a-few-tips-for-beginners)
    - [Getting started: Hands-on examples](#getting-started-hands-on-examples)
    - [How add-on code is organized](#how-add-on-code-is-organized)
    - [I don't understand those above terms](#i-dont-understand-those-above-terms)
    - [More new terms please](#more-new-terms-please)
    - [Running your add-on in this example chapter](#running-your-add-on-in-this-example-chapter)
- The add-on development guide: Introduction to app modules
    - [App module development process and strategies](#app-module-development-process-and-strategies)
    - [Differences between app modules and global plugins](#differences-between-app-modules-and-global-plugins)
    - [Example 1: Simple app module in Notepad](#example-1-simple-app-module-in-notepad)
    - [Example 2: Silencing NVDA in Openbook](#example-2-silencing-nvda-in-openbook)
    - [Example 3: Announcing control property changes while using another app](#example-3-announcing-control-property-changes-while-using-another-app)
    - [Example 4: Customizing status bars as seen by NVDA](#example-4-customizing-status-bars-as-seen-by-nvda)
    - [Introduction to app modules](#introduction-to-app-modules)
    - [Other remarks on app modules](#other-remarks-on-app-modules)
    - [Supporting multiple apps with one app module](#supporting-multiple-apps-with-one-app-module)
    - [Useful app module properties and methods](#useful-app-module-properties-and-methods)
- The add-on development guide: Introduction to global plugins
    - [Example 1: Writing computer braille using QWERTY keyboard](#example-1-writing-computer-braille-using-qwerty-keyboard)
    - [Exercises](#exercises)
    - [A Few more things to remember about global plugins](#a-few-more-things-to-remember-about-global-plugins)
    - [The global plugin code](#the-global-plugin-code)
    - [Introduction to global plugins](#introduction-to-global-plugins)
    - [Typical development plan for global plugins](#typical-development-plan-for-global-plugins)
    - [When to write or not write global plugins](#when-to-write-or-not-write-global-plugins)
- The add-on development guide: Setting Up Your Add-on Development Environment
    - [Add-on Development Folder Structure](#add-on-development-folder-structure)
    - [Add-on folder structure](#add-on-folder-structure)
    - [Packaging add-ons](#packaging-add-ons)
    - [System Requirements](#system-requirements)
- The add-on development guide: Sharing your add-on and experience with others
    - [The NV Access add-on store and code repository](#the-nv-access-add-on-store-and-code-repository)
    - [The NVDA Add-ons list](#the-nvda-add-ons-list)
    - [Publishing add-ons for community distribution](#publishing-add-ons-for-community-distribution)
    - [Sharing your add-on and experience with others](#sharing-your-add-on-and-experience-with-others)
- The add-on development guide: Useful modules from NVDA core
    - [List of useful NVDA core modules and methods](#list-of-useful-nvda-core-modules-and-methods)
    - [Some real-life examples](#some-real-life-examples)
    - [Useful modules from NVDA core](#useful-modules-from-nvda-core)
- The NVDA developer guide: Extension Points
    - [addonHandler](#addonhandler)
    - [braille](#braille)
    - [config](#config)
    - [Extension Points](#extension-points)
    - [inputCore](#inputcore)
    - [logHandler](#loghandler)
    - [nvwave](#nvwave)
    - [speech](#speech)
    - [synthDriverHandler](#synthdriverhandler)
    - [tones](#tones)
    - [vision.visionHandlerExtensionPoints.EventExtensionPoints](#visionvisionhandlerextensionpointseventextensionpoints)
- The NVDA developer guide: Introduction
    - [Add-on API stability](#add-on-api-stability)
    - [C++](#c)
    - [A Note About Python](#a-note-about-python)
- The NVDA developer guide: NVDA Python Console
    - [Namespace](#namespace)
    - [Tab completion](#tab-completion)
    - [Usage (The NVDA developer guide: NVDA Python Console)](#usage-the-nvda-developer-guide-nvda-python-console)
- The NVDA developer guide: Packaging Code as NVDA Add-ons
    - [Add-on Documentation](#add-on-documentation)
    - [Braille translation tables](#braille-translation-tables)
    - [Localizing Add-ons](#localizing-add-ons)
    - [Manifest Files](#manifest-files)
    - [Non-ASCII File Names in Zip Archives](#non-ascii-file-names-in-zip-archives)
    - [Optional install / Uninstall code](#optional-install-uninstall-code)
    - [Packaging Code as NVDA Add-ons](#packaging-code-as-nvda-add-ons)
    - [Plugins and Drivers](#plugins-and-drivers)
    - [Speech dictionaries](#speech-dictionaries)
- The NVDA developer guide: Plugins
    - [the App Module SleepMode variable](#the-app-module-sleepmode-variable)
    - [App modules for hosted apps](#app-modules-for-hosted-apps)
    - [Associating App Modules with an executable](#associating-app-modules-with-an-executable)
    - [Basics of a Global Plugin](#basics-of-a-global-plugin)
    - [Basics of an App Module](#basics-of-an-app-module)
    - [Events (The NVDA developer guide: Plugins)](#events-the-nvda-developer-guide-plugins)
    - [Example 1: An App Module that Beeps on Focus Change Events](#example-1-an-app-module-that-beeps-on-focus-change-events)
    - [Example 2: an app module for an app hosted by wwahost.exe](#example-2-an-app-module-for-an-app-hosted-by-wwahostexe)
    - [Example 3: a Global Plugin Providing a Script to Announce the NVDA Version](#example-3-a-global-plugin-providing-a-script-to-announce-the-nvda-version)
    - [Example 3: an app module for an app employing Edge WebView2 ( msedgewebview2.exe )](#example-3-an-app-module-for-an-app-employing-edge-webview2-msedgewebview2exe)
    - [Example 4: A Global Plugin to Find out Window Class and Control ID](#example-4-a-global-plugin-to-find-out-window-class-and-control-id)
    - [Example 5: A Sleep Mode App Module](#example-5-a-sleep-mode-app-module)
    - [Example 6: Command to Retrieve the Length of Text in an Edit Field Using a Custom NVDA Object](#example-6-command-to-retrieve-the-length-of-text-in-an-edit-field-using-a-custom-nvda-object)
    - [Example 7: Labelling the Notepad Edit Field Using event_NVDAObject_init](#example-7-labelling-the-notepad-edit-field-using-event_nvdaobject_init)
    - [Making Small Changes to an NVDA Object in App Modules](#making-small-changes-to-an-nvda-object-in-app-modules)
    - [NVDA Objects](#nvda-objects)
    - [Overview](#overview)
    - [Parsing additional command line arguments in your plugin](#parsing-additional-command-line-arguments-in-your-plugin)
    - [Providing Custom NVDA Object Classes](#providing-custom-nvda-object-classes)
    - [Scripts and Gesture Bindings](#scripts-and-gesture-bindings)
    - [Types of Plugins](#types-of-plugins)
- The NVDA developer guide: Remote Python Console
    - [Remote Python Console](#remote-python-console)
    - [Usage (The NVDA developer guide: Remote Python Console)](#usage-the-nvda-developer-guide-remote-python-console)
- The NVDA developer guide: Translation
    - [Character Descriptions](#character-descriptions)
    - [Gestures](#gestures)
    - [Symbol Pronunciation](#symbol-pronunciation)
    - [Translation](#translation)
- Miscellaneous
    - [Authors, Contributions, and Copyright](#authors-contributions-and-copyright)
    - [Available Add-ons](#available-add-ons)
    - [Custom braille tables and speech symbol dictionaries](#custom-braille-tables-and-speech-symbol-dictionaries)
    - [Introduction](#introduction)
    - [The message dialog API](#the-message-dialog-api)

## The add-on development guide: Add-on Basics

### Installing NVDA Add-ons

You can install NVDA-approved add-on packages via the add-on store, found on NVDA's tools menu. Alternatively, you can open any .nvda-addon file you may have created or downloaded, by selecting it in your Windows file manager, and it should launch the add-on install process.

### What Are Add-on Modules?

Add-ons can act globally (across all of NVDA), in a specific application or program, behind the scenes (at the hardware or software level), enhance NVDA experience for visual audiences, or improve speech and braille output. We call these five major areas "modules". Every add-on contains at least one module, which is just one or more Python files designed to act in one of these five specific areas.

Additionally, if it makes sense for the add-on you are developing, your add-on can include more than one module. For example, if your add-on provides better accessibility for a specific application, but also provides global commands that work anywhere in NVDA, you would be using two modules.

Currently, NVDA supports these add-on module types:

- Global plugin: A global plugin adds features for NVDA which can be used anywhere, such as OCR capability.
- App module: An app module allows enhanced support for a specific program. App modules only run as long as the program runs. They change how NVDA reacts to the windows and controls in the running application.
- Driver: A driver allows a program to talk to hardware, and in some cases, other software. Currently you can write drivers for braille displays or speech synthesizers.
- Enhancer: An enhancer is used to improve NVDA experience for different groups of users as they use computers. Currently one enhancer type, "vision enhancement provider", is supported.
- Processor and presenter: special enhancers adding custom braille tables and speech symbol dictionaries.
Note: global plugins, app modules, drivers, vision enhancement providers, and custom braille tables are housed in standalone module folders, whereas speech symbol dictionaries are part of add-on's locale folder. Custom braille table development requires familiarity with Liblouis table specification (the table format is not covered in this guide), and speech symbol dictionaries follow NVDA's speech dictionary file format documented in the NVDA development guide.

### What Are Add-on Packages?

A package is the single file which contains the code, documentation, and other elements which make up a fully functioning add-on, which is intended to be robust enough to be distributed to the public. Each NVDA add-on package is a normal zip file with a file extension of .nvda-addon instead of .zip.

If making an add-on package sounds like a lot of work: don't worry, you don't have to make a package just to start writing and testing your first add-on.

### What are Add-ons?

Add-ons are additional small programs that extend NVDA's functionality or support for applications. This may include adding global features, enhancing support for an application, supporting additional braille displays or speech synthesizers, enhancing visual usage of NVDA via vision enhancers, or adding custom processing modules for speech symbols and braille input and output.

A fully constructed add-on will consist of the add-on Python code itself, contained in one or more modules (more on that in the next section), and usually some documentation, and other support files. If that sounds daunting: don't worry, we will start small, with examples, and only with Python code. The rest of the support structure for an add-on will come later.

Note: add-ons are sometimes called "Plugins", especially in the [NVDA Developer Guide](https://www.nvaccess.org/files/nvda/documentation/developerGuide.html). Although they may appear to be similar, these terms are different:

- Add-on: one or more modules or components packaged as an archive for easy installation.
- Plugin: a module or a collection of modules designed to modify NVDA's behavior in various ways.
Throughout this guide, whenever we refer to "add-ons", you can assume that they contain at least one plugin or component.

## The add-on development guide: Add-on module components and development tips

### Add-on module components and development tips

IMPORTANT: this chapter mainly covers Python modules. Information on custom braille tables and speech symbol dictionaries will be covered later in this guide.

An add-on module consists of a number of components. This includes handling input and output, working with different NVDA objects, reacting to events, storing configuration and more.

This chapter introduces key components and concepts that are used in add-on development, such as NVDA objects, scripts, event handling and additional topics with examples.

Note that the [NVDA core development guide](https://www.nvaccess.org/files/nvda/documentation/developerGuide.html) introduces the below concepts. This chapter is intended as an extension of that document. Consult the NVDA developer guide for a brief introduction.

Note for scripters of other screen readers: you might be familiar with some of the concepts introduced in this section. Please read this section if you want a better understanding of how some of them are used in NVDA.

### Add-on planning and development tips

Over the years, the NVDA community built a number of powerful add-ons for NVDA users. Over the course of these years, the add-on writers gathered some useful tips when it comes to writing your own add-ons. Here are a number of them:

- Get to know NVDA: it is important that you become familiar with NVDA commands, concepts and tips. Subscribe to NVDA users groups to learn more about NVDA and how NVDA works, as you'll be extending it via your add-ons.
- Get to know the product at hand: as noted earlier, it is important that you get to know the software you're writing the app module for, synthesizers and braille displays you'll be writing the driver for and so on.
- Plan ahead: if you know you'll be maintaining your add-on for a number of months or years, it is useful to have a plan and write the add-on code to prepare for future extensions. For example, working on features that you need to implement now, dividing parts of a program to objects and so on.
- Ready to debug and test your add-on: writing your add-on code is just one part of the overall add-on development. The other part is testing and debugging your add-on to make sure that users use your add-on with minimal errors. As you write your add-ons, be sure to test your code regularly.
- Most importantly, have fun.

### Do's and don'ts

Here are a few things you should do and not do throughout add-on development:

- Do talk with users: it is important to remember that your add-ons will be used by NVDA users around the world, so it is important to keep in touch with your users to gather bug reports and suggestions.
- Do ask for help if needed: If you're stuck, you can ask other add-on writers anytime for solutions or tips, or if you need to, ask for collaboration from other add-on developers.
- Do test your add-on on more than one computer: sometimes, a bug in one computer may help you solve problems with your add-on on your computer later.
- Don't use fancy code without understanding your intentions: a typo or forgotten indentation can become troublesome when you debug an add-on.
- Do keep up to date with NVDA core changes: sometimes, you may find that your add-on might not work due to NVDA core code changes. Be sure to read "changes for developers" section in NVDA's What's New document to keep up to date with code changes that may affect your add-on.

### Events (The add-on development guide: Add-on module components and development tips)

You can ask NVDA to do something if something happens. For example, you can ask NVDA to say the new name for an object when it's name changes, or say the new item's value when the item gets focused. These conditions, or actions are called events.

When an event occurs, NVDA does the following:

- Finds out what the event was (for example, a check box gains focus).
- Performs actions for the event (e.g. says the name and the checked state of this check box).
- Passes the event down the chain in case other objects may have actions associated with the event.
Depending on where the event is defined, you'll need two or four things when defining an event. If it is declared from the add-on module, the required parts are event name, the add-on module (self), object and next handler in case the object has other events associated with it. If it is defined as part of an object, the name of the event and the object (self) is required.

A typical event routine looks like this:

    	def event_eventName(self, obj, nextHandler):
    		# Do some action.
    		nextHandler()

For object events, use:

    	def event_eventName(self):
    		# Event routine.

In fact, we have met an actual "event" before: `event_NVDAObject_init`. This is a special event (one of many events defined in NVDA) fired when NVDA meets a new object and initializes it according to your input (see the section on overriding object properties for more information). Let's meet other events you may see while writing your add-on.

### Events within objects

The above section described event routines from an add-on's perspective. This is just one way of defining events. The other way is to define events from within objects, and is same as above except that it only takes one argument (self).

### Examining object hierarchy

There are a number of ways which you can use to see the hierarchy of an object for a given program:

- Using object navigation commands (NVDA+Numpad 2/4/5/6/8) with simple review mode turned off.
- Using [Python Console](https://www.nvaccess.org/files/nvda/documentation/developerGuide.html#PythonConsole), use obj.next/previous/parent/firstChild/lastChild attributes. If you want to see all available properties, from Python Console, type dir(obj).
If you wish to see a more detailed description about the navigator object, while the navigator object is located at the object you're interested in, press NVDA+F1 to launch log viewer and examine the developer info shown. The root of all objects in Windows is the desktop, or shell object.

### Example 1: Finding the value of a slider in a program

Suppose you are asked by a user to give him the value of a slider in a program using an app module. After looking at the object hierarchy and other properties, you know that the toolbar is the last child of the foreground object.

Here is the code to implement this feature:

    # Object example 1

    import api
    import appModuleHandler

    class AppModule(appModuleHandler.AppModule):

    	sliderChildIndex = -1 # The variable to store the child index.

    	def getSliderValue(self):
    		fg = api.getForegroundObject()
    		sliderVal = fg.children[self.sliderChildIndex].value
    		return sliderVal

In this code, the method `fg.children[index]` is used to retrieve the child with the given index (here, since we said the toolbar is the last child, the index would be minus 1, or the very last child; we could have used fg.lastChild). Alternatively, you can use `fg.getChild(-1) in certain situations (IAccessible, for example).)

However, this code has an issue: what if the slider value is actually within the first child of the actual slider control? One way to fix this is to check the object's role. The modified code looks like this:

    	def getSliderValue(self):
    		from controlTypes import Role # It is possible to import from within a method.
    		fg = api.getForegroundObject()
    		slider = fg.lastChild
    		if slider.role == Role.SLIDER: return slider.firstChild.value

Thus, when we know for sure that we're dealing with the slider, the method returns the value of the slider's first child (if that is the case). Note the two equals signs for equality, as opposed to just one equals sign for assignment.

There are other examples you can try to familiarize yourself with object navigation and manipulation:

- Obtaining the name of an object that is located somewhere else in the program.
- Moving the navigator to the foreground object.
- Setting focus to another program.
- Locating the first status bar in a program with multiple status bars.
For real-life examples on objects in NVDA, consult the NVDA source code or source codes of various community add-ons.

### Example 2: A basic script dictionary and message output

In this example, we'll define two scripts called "sayHello" and say"GoodBye", then bind them into two separate gestures.

    	# An example fragment for script assignment from a global plugin.
    	import ui

    	def script_sayHello(self, gesture):
    		ui.message("Hello!")

    	def script_sayGoodBye(self, gesture):
    		ui.message("Good Bye!")

    	__gestures={
    		"kb:control+NVDA+1":"sayHello",
    		"kb:Control+NVDA+2":"sayGoodBye"
    	}

Now when you press Control+NVDA+1, NVDA will say, "Hello", and when you press Control+NVDA+2, NVDA will say, "Good bye." This is the basic code on receiving commands and sending messages.

### Example 3: script information using script decorator

As we have seen with an example above, script decorator can be used to assign gestures to scripts easily. But script decorator can do more than assign gestures: it can be used to provide additional information such as input help message or let the script participate in speech on demand mode.

In addition to the modified example 2, the below example will add an input help message for both scripts, along with setting Control+NVDA+3 to make NVDA say "good bye", the latter available in speech on demand mode.

    	# An example fragment for script decorator usage from a global plugin.
    	import ui
    	from scriptHandler import script

    	@script(
    		description="Says Hello",
    		gesture="kb:control+NVDA+1",
    	)
    	def script_sayHello(self, gesture):
    		ui.message("Hello!")

    	@script(
    		description="Says good bye",
    		gestures=["kb:Control+NVDA+2", "kb:Control+NVDA+3"],
    		speakOnDemand=True,
    	)
    	def script_sayGoodBye(self, gesture):
    		ui.message("Good Bye!")

#### Script decorator arguments

You can pass in the following information about a script to the script decorator:

- description: short script description. This will be presented in input help mode and in input gestures dialog.
- category: the category associated with this script, used to group the script under an appropriate category in input gestures dialog.
- gesture: a single gesture bound to the script.
- gestures: a list of gestures bound to this script.
- speakOnDemand: set it to True to make the script available in speech on demand mode; default is False.

### Example 4: Scripts for specific objects

As in specialist objects above, scripts can be assigned to certain objects by specifying gestures dictionary for this particular object. Here is an example from an app module which defines scripts for main window of a media player program, defined using script decorator and made available in speech on demand mode:

    # Scripts for objects for a program.
    # By default, speakOnDemand is False (unavailable in speech on demand mode).
    from NVDAObjects.IAccessible import IAccessible
    from scriptHandler import script

    class Player(IAccessible)

    	@script(gesture="kb:NVDA+T", speakOnDemand=True)
    	def script_saySongName(self, gesture):
    		ui.message(self.songTitle_) #Suppose if that variable has been defined.

    	# And in the main app module:
    	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
    		if obj.windowClassName == "PlayerWindow": clsList.insert(0, Player)

There is something odd going on with this example: normally, when you press NVDA+T, NVDA says the title of the current window, but in this example, it announces the name of the song instead. This is the result of script lookup (see below) where the script for the current object is run instead of title script from global commands. This is a common way of binding new scripts at runtime.

### Example 5: Announcing the changed name of a control

The following code came from one of the add-on app modules.

Below is a routine for an event which tells you the name of some text on the screen when the text changes.

    	def event_nameChange(self, obj, nextHandler):
    		if obj.windowClassName == "TStaticText": ui.message(obj.name)
    		nextHandler()

As you can see, whenever the text object's name changes, NVDA will announce the new name to the user. The "name change" event is one of the many events that you can define custom actions for in your add-on (the complete list is below).

Note: You can define events for any object of your choice, especially controls in a program (where you can define custom actions for events in your app module). If this is the case, you need to make sure that the control meets certain conditions you set, such as name, role and so forth to let NVDA keep an "eye" on that specific object.

### Examples of overlay classes and modified roles

Below examples illustrate the uses of the two overlay and attribute modification methods we've discussed above:

An example of the first case: modifying an attribute.

    	# Reassign some Delphi forms as window.
    	import controlTypes

    	def event_NVDAObject_init(self, obj):
    		if obj.windowClassName == "TForm": obj.role = controlTypes.Role.WINDOW

This means that whenever we encounter a window with the class name of "TForm", NVDA will treat this as a normal window.

Example 2 deals with an app module which has two objects for dealing with specific parts of a program, then uses chooseNVDAObjectOverlayClasses to assign the logic for each control.

    #An example of overlay classes

    class enhancedEdit(IAccessible):
    	# Some code to be run when window class name is MyEdit.

    class MainWindow(IAccessible):
    	# Another code, this time adding custom gestures for main window of the program.

    # In the app module:

    def chooseNVDAObjectOverlayClasses(self, obj, clsList):
    	if obj.windowClassName == "myEdit": clsList.insert(0, enhancedEdit)
    	elif obj.windowClassName == "TWindow": clsList.insert(0, mainWindow)

In both cases, the object that we wish to check must be inserted as the first element of the clsList. The effect is that these custom objects will take precedence when looking up gestures or code (behavior) for the object, and in the developer info, these custom objects will come first when MRO (Method Resolution Order) for the navigator object is displayed.

Note: You may need to tune these two methods to provide correct overlay classes for very specific controls (such as checking names, specific roles, etc.), otherwise you may find that two or more identical-looking controls are assigned to your custom object when in fact they are very different. Also, the event_NVDAObject_init is only available in app modules.

### A few other remarks on scripts

- You can use any modifiers as parts of commands for scripts (for example, Alt+NVDA+letter). However, in order to avoid command conflicts, try minimizing use of commands that programs might use such as Control+letter, Alt+Shift+letter and so on.
- When assigning keyboard commands, keyboard key labels are case insensitive.
- You can define a script category to show the user where your add-on script will be used (shown in Input Gestures dialog). There are two ways of doing this: module level via `scriptCategory` attribute from the add-on module, or designating the category for each script via either `script_name.category` attribute or as part of script decorator by defining the category argument. It is recommended that you name your script category the same as the add-on name.
- You can define the input help mode message for a script by either using `__doc__` attribute (commonly known as docstrings) or by passing in a short description to description argument of script decorator. Script description is also used in Input Gestures dialog to show the description for a script.
- If you need to leave one or more scripts unassigned (for example, if a gesture conflicts with a global command), do not include the gesture binding for the script in the gestures dictionary or do not define gesture/gestures argument in script decorator. This helps minimize gesture conflicts and allows users to assign custom gestures for scripts.
- If there are two objects, A and B and if B inherits from A and both contain same command for a script, you can assign "None" to script name in object B (subclass) to bypass a command when dealing with commands from object B. For example, if F10 is defined for both objects and F10 is not used in object B, you can assign object B's F10 command to "None" so F10 can be sent to the operating system. This is implemented in some NVDA core modules and in StationPlaylist Studio add-on.

### Focus vs. navigator object

In your add-on, you might wish to work with various objects and manipulate them. These may include changing the focused object, synchronizing navigator and focus objects, changing the role of an object and so on.

A focus object is the currently focused control. These are linked to keyboard focus - that is, it follows the highlighted control. In contrast, a navigator object is the object you're interested in. Since navigator objects can move anywhere, you can examine two objects at once: the focused object and the navigator object. For instance, you might be focused on an edit field while examining the title bar as the navigator object. We already saw an example above where we can check if we're on two different apps by checking for app modules for focus versus navigator object.

In your add-on, to fetch the object with focus, write `someObj = api.getFocusObject()`. The someObj can be named differently - the convention is to use the name "obj". To fetch the navigator object (which might be different from the focused object), use `obj = api.getNavigatorObject()`.

### Frequently Asked Questions about add-on components and development

Q. When I try to obtain an object using an index, it fetches an object one after the index I wrote.

This is the side effect of zero-based indexing (count starts at 0).

Q. When importing a module, NVDA says it cannot locate the module.

Did you type the correct name of the module? Did you extract the module files in the correct location? Try fixing the typo, look at the import path and try importing again.

Q. What is the difference between simple review and normal review and which one should I use?

Simple review excludes layout objects such as windows, grouping and so on which are placed for layout purposes. Normal review includes these as well. The choice of using simple review or normal review depends on your situation.

Q. The command for my app module does not work in my app module; instead, NVDA does something else.

Check if a global plugin which uses the command is installed. First, disable the global plugin and try again.

Q. How can I use Win32 API in my add-on or object?

There is a document written by an add-on developer which talks about using Win32 API in your add-on. Select [this link](http://www.zlotowicz.pl/nvda/winapi.mdwn) to view this document.

Q. How can I create dialogs in my add-on?

See the Interactive Dialogs section.

Q. Can I create functions and assign variables outside the module classes?

Yes. This is useful if you need to reference them from inside the add-on class. For example, you may have a function that's defined outside your class that you'll need to use from more than one method in a global plugin class.

Q. I want to save user settings for my add-on. Can this be done?

Yes. You'll need to use a library that allows persistence, such as ConfigObj library (configObj), JSON, or pickle to manage configuration. Some add-ons (such as OCR) which use configuration files store their configuration as an ini file in NVDA's user configuration folder. For global plugins, you can load and save user configuration from the add-on when the add-on is created (init) or finished (terminate), respectively. You cannot do this easily with app modules. Also, you'll need to provide a facility (commands, dialogs, etc.) where users can configure add-on settings.

Q. I have a script which calls a function that runs for a long time, and I cannot run NVDA commands when my script runs.

One way to fix this is using threads (separate, independent operations in a program) via Python's threading module. In order to do this, create a method which you know will run for a long time, then from the script which calls this method, create a new thread (see Python's threading module documentation) that'll be in charge of running this method. This way other NVDA commands can be performed while the add-on method does its work (see Google Speech Recognition module for an example code).

Q. I would like to port a module written in Python 2 syntax for use as an NVDA add-on.

This cannot be done easily. One handy module for this purpose is six, which allows running Python 2 and 3 code. NVDA 2019.3 and later is strictly a Python 3 release, and from January 2022 onwards, Python 3 is required.

Q. My add-on uses GUI facility, and after installing NVDA 2018.3, I get errors related to wxPython.

NVDA 2018.3 uses wxPython 4, whereas earlier versions use older wxPython releases. If you want to support older NVDA releases, you need to use conditional statements (if/else) and version checks so the appropriate code path can be used.

Q. After installing NVDA 2019.1, users say my add-ons are not compatible.

NVDA 2019.1 introduces add-on compatibility flags (sometimes called compatibility range) that tells NVDA the following information:

- Minimum NVDA version (minimumNVDAVersion): an add-on can specify minimum NVDA version required for the add-on. This is useful if you need to use features introduced or changed in a given NVDA release without supporting older NVDA releases.
- Last tested NVDA version (lastTestedNVDAVersion): tells NVDA the highest tested release for the add-on. Without this flag being set, NVDA will treat your add-ons as incompatible with the latest release.
Words in parentheses are manifest keys. Starting in NVDA 2019.1, these compatibility flags are mandatory for all add-ons.

Q. My app module that was stored under appModules folder in user configuration folder isn't working in NVDA 2019.1.

This is because NVDA 2019.1 will not load custom extension code stored in subfolders of user configuration folder anymore. See the section on scratchpad for details.

Q. Should I convert gestures dictionary and script docstring attribute to script decorator?

It is up to you whether or not you wish to use older gestures dictionary and script docstring or the newer script decorator to define script information. For new add-ons, script decorator is preferred for easily defining script information on the spot.

Q. I want my script to say something in speech on demand mode.

If your add-on includes scripts to announce information, you can let the script participate in speech on demand mode by setting "speakOnDemand" to "True" in the script decorator (see speech on demand script example above for details).

Q. Is there anything to know about speech on demand mode?

Speech on demand mode is designed to let NVDA provide informational messages such as screen content when some commands are performed while silencing announcements from other commands. Depending on your needs:

- Offer speech on demand mode if announcing critical screen content using keyboard commands or report information gathered via the add-on on demand.
- Do not define "speakOnDemand" if the script changes add-on or NVDA settings or perform operations such as navigating to a different screen area or opens dialogs.
Q. What is the recommended coding style for add-ons?

The following is baseline coding style for add-ons, deriving from NVDA screen reader coding style:

- Use tab for indentation.
- Use camel case for function and variable names e.g. someFunction.
Q. I noticed that NVDA does not come with all Python libraries.

Most notably, NVDA earlier than 2024.1 does not ship with asyncio. You must include additional libraries inside your add-on component folder.

Q. I need to manipulate environment variables such as system path.

An effective way to do this is prepending a desired string (such as the path to an executable you need to run) to existing environment variable value. This allows your add-on to work with modified values without breaking NVDA and/or Windows components while NVDA is running.

Q. After installing NVDA 2022.1, parts of add-ons that use control types module report errors.

Control types module (controlTypes) was refactored in NVDA 2021.2 which was completed in 2022.1. Specifically, roles and states definitions have changed from ROLE_/STATE_ to Role.* and State.*, respectively. You can support older and newer NVDA Releases by doing an attribute check (hasattr) for role and state constants.

Q. Why are add-on commands still available when NVDA is running on secure screens?

It is possible to disable parts of add-ons such as global plugins by checking for globalVars.appArgs.secure flag in their constructor (init method) and returning early if this flag is set. However, this only affects class attributes defined in the constructor. Because scripts are defined at the class level, add-on commands can be performed from secure screens.

You can disable the affected add-on class (global plugin or app module) using one of the following methods:

- Module organization: define the affected class in a file other than the main module file, then from init.py file, import the affected class if secure flag is off.
- Decorator: a decorator that will return either the passed in class or the default implementation from NVDA if secure flag is off or on, respectively.
Q. What are other security issues to consider when handling NVDA on secure screens?

In addition to script execution noted above, the following issues should be considered when running add-ons in secure screens:

- Web access: while add-ons can use modules to access information over the network such as websites, this is a security risk as users can browse to a different website or files can be downloaded by malicious actors.
- File operations: add-ons can perform file and folder operations such as creating, renaming, deleting, reading, and writing files and folders, and this is a security risk if performed from secure screens.
Unless the add-on is designed for these tasks in mind from secure screens, your add-on should keep the above issues in mind. The best action is advising users to not install affected add-ons to secure screens.

Q. My speech add-on does not work after installing NVDA 2025.1.

If the add-on wants to know the audio output device at startup as part of nvwave.WavePlayer call, the path for obtaining this data has changed in NVDA 2025.1 from config.conf["speech"]["outputDevice"] to config.conf["audio"]["outputDevice"]. You can use one of the following workarounds:

- Import buildVersion at the top of the module, then create a variable to record either "speech" or "audio" depending on version, then pass in this string variable when calling nvwave.WavePlayer's outputDevice parameter (config.conf[variable]["outputDevice"]).
- Use dict.get method to obtain the output device (config.conf["speech"].get("outputDevice", config.conf["audio"]["outputDevice"]).
- Do not specify outputDevice argument in nvwave.WavePlayer as NVDA itself will fetch the default audio output device.
We did not include programming or Python-related FAQ's, as there are sites which answer questions about Python such as coding style. Consult these documents if you have issues with Python code.

Now that we have covered basic add-on components, let's learn about how to package what you know in your add-on modules themselves: global plugins, app modules, drivers, and enhancers. If you are looking for information on custom braille tables and speech symbol dictionaries, skip the next four chapters.

### Input and output: scripts and UI messages

Another crucial component of add-ons is handling commands from users and displaying what the add-on is doing. These are done via scripts (input) and UI messages (output).

A script is a method run when the user performs certain commands. For example, when you press NVDA+T, NVDA runs a script in global commands module called SayTitle. In Poedit, for instance, when a translator presses Control+Shift+A, NVDA will read translator comments added by the programmer to help clarify a given translatable string. This command is not a native NVDA command, but it is defined in the Poedit app module to perform this function.

Typically, an add-on which accepts scripts will have a list of command:function mapped somewhere in the module. The simplest is a gestures (commands) dictionary, a python dictionary (typically named __gestures) which holds commands as keys and scripts as values for these keys (more than one key, or command can be bound to scripts). Alternatively, information about each script such as its description and bound gestures can be specified through script decorator. These dictionaries are loaded when add-on loads and are cleared when either NVDA exits or the app for the app module loses focus (that is, the user has switched to another program).

Another way to bind scripts is via runtime insertion. This is done by creating another gestures dictionary apart from __gestures dictionary which holds context-sensitive gestures such as manipulating a single control. Then the developer would use inputCore.bindGesture (or inputCore.bindGestures if more than one gestures/scripts are defined) to define certain gestures for a time, then using inputCore.clearGestures then inputCore.bindGestures(__gestures) to remove the added gestures. A more elegant way, which involves scripts for specific objects, will be covered when we talk about app modules and assigning gestures to specific parts of a program.

For most scripts, you don't have to worry about sending the command to the application. However, in case the script performs additional tasks while sending the key to the active application, you can use `gesture.send()` to send the command first before performing additional work.

In a similar manner to scripts, the UI module allows you to say or braille what your add-on is doing. This is done by using `ui.message(something to say)` where `something to say` is replaced by a string for NVDA to say. Alternatively, you can call speech and braille handler methods directly if you want speech to say one thing and the braille display to show something else. We'll not go over `ui.message` here (you'll see examples of those), but what's more important is scripts, so we'll focus on that in this section.

As of 2025, NVDA supports input from the keyboard, braille displays with or without braille keyboard and touchscreens. These input types have a corresponding gesture prefix (kb for keyboard, br for braille and ts for touchscreen) which identifies the type of gesture. Output can be sent via speech and/or braille.

### Let's build an add-on

Now that we have a basic overview of components of add-ons, we're ready to build some simple add-ons. But first, let's go over the actual add-on development process, debugging tips, do's and don'ts and other tips.

### List of possible events

This is a list of common events you may define custom actions for in your add-on:

- gainFocus: The user has moved the focus to a specific control, or the user has just switched to a program.
- loseFocus: Opposite of gainFocus.
- nameChange: The name of a control has changed (see above for an example).
- valueChange: The value of the control such as text of a field has changed.
- stateChange: Useful to keep track of whether check boxes, buttons and other control's state (checked, selected, etc.) has changed.
- foreground: the object we're interested in has become the foreground window of the program.
Less common events that are used in specific situations include:

- typedCharacter: the user has entered something on a keyboard.
- appModule_gainFocus: user has switched to the app where an app module is defined. Common uses include adding touchscreen commands for specific apps, announcing extra info about the current state of the app and so on.
- appModule_loseFocus: opposite of appModule_gainFocus.
- descriptionChange: the description for a control provided by the accessibility API has changed.
- suggestionsOpened: used in controls where one can type something and suggestions will be shown based on entered text. The default implementation in NVDA plays a sound to indicate appearance of suggestions.
- suggestionsClosed: opposite of suggestionsOpened. The suggestions events require the object to derive from `NVDAObjects.behaviors.InputFieldWithSuggestions` class.

### Other components

Besides objects, scripts and events, you can add other components in your add-on for working with specific controls. For example, you can use a textInfo module (such as NVDAObjects.NVDAObjectTextInfo) for working with text and text offsets in edit fields and other controls, or use external modules from third-party developers for specialized tasks such as windows registry access (_winreg) and others. You can also use Python's built-in modules (such as time, functools, etc.) for advanced operations.

One notable component is text infos, a way to let add-ons gain access to text located on objects. You can access text, move around in it (such as via lines and words), and manipulate portions via marking ranges and offsets. For most add-ons, it isn't required to define custom text infos, as the underlying accessibility API will provide suitable information.

Another useful component is mathematical text presentation library (mathPres). This is used to allow NVDA to access math content in places such as web browsers, as well as for add-ons to define custom math presentation layers and ways to access math content in various applications. So far, math content retrieval is done on text marked with MathML with MathPlayer installed.

If you wish to store settings for your add-on, use ConfigObj or NVDA's built-in configuration manager to store configuration files and settings. ConfigObj defines settings as a collection of dictionaries that can be updated in real time. You can also pass in validation map to allow NVDA's configuration manager (config.conf)to validate settings for your add-on and let add-on settings become profile-specific settings.

Finally, you can ask NVDA to perform some routines while the add-on is loading or being terminated. This is done by defining `__init__` (constructor) and `terminate` method for the add-on. Depending on the plugin type, use:

- For global plugin:

        def __init__(self):
    		# The routine to do when the global plugin loads.
    		# Warning! You should always call super method first in order to initialize various foundations correctly.
    		# You will see actual examples of its use later in this guide.
    		super().__init__()

- For app modules:

    	def __init__(self, *args, **kwargs):
    		super().__init__(*args, **kwargs)
    		# What NVDA should do when the app module loads.
    		# You will see actual examples of its use later in this guide.

- For terminating, regardless of the add-on type:

    	def terminate(self):
    		# Do something when the add-on terminates.
    		# Warning! Never initialize ANY core module such as GUI in terminate method as doing so will prevent NVDA from exiting properly.

### Other useful object-related goodies

Here are some other methods which work with NVDA objects, all located in api.py module:

- If you wish to obtain the foreground object (useful if you wish to look at some child object of the foreground window), use `obj = api.getForegroundObject()`. The name of the foreground object, usually the top-level window of an application is treated as a title by NVDA and can be obtained by pressing NVDA+T.
- From [Python Console](https://www.nvaccess.org/files/nvda/documentation/developerGuide.html#PythonConsole), to see the number of child objects that an object contains (for instance, the children, or widgets of a foreground window), type `obj.childCount`. The value 0 means that there are no more child objects.
- To set some object as the new focus or navigator object, use `api.setFocusObject(obj)` or `api.setNavigatorObject(obj)`. These do not change what Windows views as focused object, as these change what NVDA thinks is the focus and navigator object.
- You can fetch various properties of an object by specifying obj.property where property is the attribute you wish to see (e.g. obj.value). Common properties include name, value, states, role, app module, window class name and so on.

### The Python Console

This guide sometimes suggests that you use the [Python Console](https://www.nvaccess.org/files/nvda/documentation/developerGuide.html#PythonConsole). The console is a feature of NVDA which can be very useful to developers. It is described in more detail in chapter 5 of the [NVDA Developer Guide](https://www.nvaccess.org/files/nvda/documentation/developerGuide.html). You can activate it by going to the NVDA Tools menu, or by pressing NVDA+control+z.

### Script lookup order and command conflicts

As you write add-ons with scripts, you need to remember the following script lookup order when trying to assign commands to scripts:

- Global plugins.
- App modules for the currently focused program.
- NVDA objects we're dealing with.
- Global commands.
For example, if you assign the command NVDA+Shift+Y to an app module script, NVDA will run that script from that program since no global plugin is using this command. However, if a global plugin which uses that command is installed, the script from the global plugin will be run instead of the app module script. Similarly, from the above example, when using programs other than that media player, NVDA will run a command from the global commands collection when NVDA+T is pressed; but as long as we're using this media player, NVDA+T will announce the name of the song (NVDA objects in app modules take precedence).

Because of the above rule, one should be careful when defining a script for an add-on. To help you with this, keep the following guidelines handy:

- First, consult the NVDA commands quick reference to see if the command you wish to use has been defined in global commands. You should try to minimize conflicts with built-in NVDA commands. An exception is commands for app modules where same command may be used differently from one program to another.
- Read the documentation for add-ons (especially global plugins) to see if any add-on is using this command, and if so, contact the add-on author to come up with an alternate binding.

### Specialist objects and overriding object properties at runtime

Sometimes, it is not enough to work with default behavior for a control. For example, some parts of a program may need custom gestures, or one may need to change the role of a window to that of a button.

NVDA provides two methods for creating or manipulating specialist, or overlay objects (or classes), each suited for different needs:

- `event_NVDAObject_init(self, object we're dealing with)`: If you wish to override certain attributes of a control such as its role or label (name), you can use this method to ask NVDA to take your "input" into account when meeting objects for the first time (or initialized). For instance, if the control has the window class name of TForm (seen on many Delphi applications), you can ask NVDA to treat this control as a standard window by assigning obj.role = controlTypes.Role.WINDOW (see control types module for list of available roles).
- `chooseNVDAObjectOverlayClasses(self, object, list of classes)`: This allows NVDA to use your own logic when dealing with certain objects. For example, this is useful if you wish to assign custom gestures for certain parts of a program in your app module (in fact, many app modules define objects to deal with certain parts of a program, then uses chooseNVDAObjectOverlayClasses to select the correct object when certain conditions are met). These custom objects must be based on a solid object that we wish to deal with (mostly IAccessible is enough, thus most overlay objects inherit from, or is the child or specialist class of IAccessible objects). In certain situations, you can use this method to drop a property from an object, such as telling NVDA to not treat this object as a progress bar by removing progress bar behavior from this object.
Note that in case of the second method, the class(s) with the given name must be present in the file, which is/are inherited from a known base object (in Python, the syntax for the inheritance is `childClass(baseClass)`, and is usually read as, "this child class inherits from this base class". We'll see code like this later).

### Working with objects on screen

An object is an instance of a class - that is, a class coming to life while a program is running. For example, if a class called button has been defined, the button on a screen is the object of this button class.

In NVDA, an object is a representation of a control or part of a program. This includes buttons, check boxes, edit fields, toolbars, sliders and even the application window. These are organized into hierarchies, or parent-child relationships where an object may contain child objects - for example, a list object in Windows Explorer may contain one or more list items, and the parent of this list might be the Windows Explorer window. The object that you're examining right now is termed "navigator object."

The NVDA object (or simply called object) contains a number of useful properties or attributes. These include the object's name, its value (checked, text of the edit window, etc.), role (check box, window, embedded object, etc., location (screen coordinates) and more. NVDA objects also contain useful methods for manipulating them, such as changing the value of the object, reacting to events for the object (gains focus, value has changed, etc.) and so on.

In many situations, an NVDA object may belong to a class of related objects. For each object class, NVDA provides ways of handling it. These classes include IAccessible, JAB, UIA and so forth. These classes and behaviors for each class of objects are defined in NVDAObjects directory in the NVDA source code, and to use them in your add-on, import the appropriate object class handler for the object you're using (e.g. if you're working with an IAccessible object, import NVDAObjects.IAccessible.).

Two of these object classes merit special mention: virtual buffers and tree interceptors. A tree interceptor allows NVDA to work with a "tree" of objects as though they are just one object. A special case of tree interceptor is virtual buffer, which allows NVDA to work with complex documents such as PDF documents. These objects contain a special mechanism to determine whether a given keyboard command will be passed to the application or handled by NVDA (for instance, browse mode where first letter navigation is used to move between elements).

## The add-on development guide: Advanced Code Examples and Features

### Advanced Code Examples and Features

This chapter is a work in progress. If there is something you would like to see here, or if you have a comment or correction, please contact one of the maintainers, or ask for it on the add-ons mailing list.

### Defining add-on specific command-line options

#### Introduction

NVDA offers several command-line options (switches) to change its operation. These include "--disable-addons" to disable add-ons at startup, "-s" to start in secure screen mode, and "--install-silent" to silently install NVDA. A complete list of available command-line options can be found inNVDA's user guide and any of these can be added while specifying NVDA's executable path or from Windows Run dialog.

Add-ons can also add their own command-line options. For example, an add-on can disable specific settings from the command line or enable experimental flags or behavior when specified in Run dialog. A notable add-on with command-line options is StationPlaylist, and add-on specific command-line options change how add-on settings are loaded and managed.

#### Command-line options processing mechanics

Once specified, all command-line options are recorded in `sys.argv` (array of argument values at program startup). This list is then converted into flags stored in `globalVars.appArgs. For example, the "-m" option to disable startup sound and other routines is initially housed in `sys.argv`and then converted into`globalVars.appArgs.minimal`flag. Command-line options NVDA is unaware of are then stored in`globalVars.unknownAppArgs` list, including add-on specific switches.

While loading add-ons, NVDA will iterate through handlers bound to `addonHandler.isCLIParamKnown` accumulating decider. Any add-on wishing to define and parse command-line options must include a global plugin (this is also a must even if the add-on solely consists of app modules) with a function to process add-on specific options such as setting up flags for use by add-on components. The function is then registered as a respondent to `addonHandler.isCLIParamKnown` decider as part of the global plugin constructor.

#### Example: handling add-on specific command-line options

The following code, adapted from StationPlaylist add-on, provides a minimal example of command-line processing:

    import sys
    import globalPluginHandler

    # Process add-on specific command-line options.
    def processArgs(cliArgument: str) -> bool:
    	splAddonCLIParems = ("--spl-configinmemory", "--spl-normalprofileonly")
    	if cliArgument in splAddonCLIParems:
    		sys.argv.remove(cliArgument)
    		return True
    	return False

    class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    	def __init__(self):
    		super().__init__()
    		addonHandler.isCLIParamKnown.register(processArgs)

#### Notes on add-on specific command-line processing

- Add-on specific command-line processing is useful if you wish to let users test experimental features or change add-on behavior provided that users understand the consequences. Due to this, any custom command-line options defined by the add-on must be documented with effects clearly stated.
- Command-line processing must occur inside a global plugin. This means even if an add-on consists of ap modules, a global plugin must be included if it wishes to define its own command-line options.
- Both the command-line options processor and the call to register this processor must be part of the global plugin, the latter as part of the global plugin class constructor.

### Interactive Dialogs

#### Introduction

To present straight forward information to your users, ui.message and ui.browseableMessage are usually sufficient. However, if the user needs to give information back to your add-on, those aren't going to help. For that, you need dialogs. Creating dialogs and the many considerations around using them are outside the scope of this document, but we can help to get you started.

To create and use dialogs, you need to import two modules: GUI (import gui) and WXPython (import wx). Read their documentation to learn more about the large number of options available to you.

In short:

- gui provides methods for constructing and displaying some standard dialogs.
- wx provides the actual implementation for those dialogs, and supplies many of the constants and extended options you will need to really make use of dialogs effectively.

#### Example 1: A Basic Dialog

The following code will create a basic dialog, providing the user with two very familiar options. See the notes after the code to understand what is going on.

    import wx  # We need this for working with dialogs and windows

    import gui  # We need this for working with dialogs and windows
    import globalPluginHandler
    from scriptHandler import script

    class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    	# Describe the attributes of the script to NVDA.
    	@script(
    		gesture="kb:nvda+shift+t",  # Configure the key
    		description="Run an add-on guide example"  # NVDA input help, may show in Input Gestures
    	)
    	def script_makeExampleWindow(self, gesture):	# A normal GlobalPlugin script method
    		def showExampleWindow():			# Define an internal (nested) function
    			gui.messageBox(  # An NVDA function to safely create message dialogs
    				# Translators: a message shown to users as an example.
    				_(
    					"Warning! You are about to do nothing. But you will be doing it with "
    					"an important looking dialog window. Continue?"
    				), "Example Question Window", wx.OK | wx.CANCEL | wx.ICON_WARNING)
    		wx.CallAfter(showExampleWindow)

If you save the above as a global plugin and load it in NVDA, then press NVDA+shift+t, you should find yourself in a new window. The window is generated by the call to gui.messageBox. The first parameter is the text of the window, the second parameter is the title of the window, and the third parameter contains a list of constant flags which wx uses to generate the dialog's buttons and other attributes.

- wx.ICON_WARNING, causes the window to behave as a Windows warning.
- wx.OK, causes the window to display the standard OK button.
- And wx.CANCEL is the same for cancel.
Unfortunately, if we just call gui.messageBox directly, it will usually cause NVDA to hang, unless it is run from the main thread. To get around that problem, we use wx.CallAfter to queue the dialog for display in the main thread. However, wx.CallAfter can not call gui.messageBox directly: it must do so through some other method or function. In this example we achieve that by using a nested function, which only exists to call that single dialog when the script is run. We could have just as easily put this function somewhere else and not nested it; this was only done for example simplicity.

Exercise for the reader: do you notice anything important we forgot to do for the title string of the dialog? Here's a hint: we did do it for the message stringg.

#### Example 2: A Three-Way Dialog

Below is a more complex example, that shows how to return information from a dialog, based upon which button was pressed. Note that there are many more constants you can use, and types of dialog other than messageBox. This section is only an introduction to the subject to get you started.

    import wx

    import gui
    import globalPluginHandler
    from scriptHandler import script

    class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    	@script(
    		gesture="kb:nvda+shift+t",  # Configure the key
    		description="Run an add-on guide example"  # NVDA input help
    	)
    	def script_askPointlessQuestion(self, gesture):
    		"""This script prompts the user with yes/no, and returns the result as a string."""
    		def askTheQuestion():
    			# This nested function asks the user a yes/no question, and also offers a cancel
    			# option. The yes/no is returned ; or the dialog is closed on cancel.
    			result = gui.messageBox(
    				"Warning! You are about to answer a pointless question.\n"
    				"Fortunately you have this great window to do it in!\n"
    				"Do you wish to proceed?",
    				# Translators: the title of a dialog which asks the user a pointless question.
    				_("Pointless Question"), wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL)
    			if result == wx.YES:
    				# Translators: optionally shown to the user if "yes" was chosen in the Pointless Question dialog.
    				answer = _("yes")
    			elif result == wx.NO:
    				# Translators: optionally shown to the user if "yes" was chosen in the Pointless Question dialog.
    				answer = _("no")
    			else:
    				# Cancel was chosen or the dialog was closed by other means.
    				return
    			# Getting this far means that either yes or no was chosen.
    			# Let's report the answer to the user.
    			gui.messageBox(
    				# Translators: a message in a dialog showing a variable answer to the user.
    				_(f"You answered {answer} to the pointless question."),
    				# Translators: the title of a dialog showing information to the user.
    				_("Pointless Answer"), wx.OK
    			)
    		# Ask the question to the user, by calling the above nested function.
    		wx.CallAfter(askTheQuestion)

When you run this script, a dialog is created. It contains some text, and three buttons: yes, no, and cancel. As you can see, a flag is given to WX that tells it that the no button should be the default--this is optional of course. Then we use wx.CallAfter to run the nested function. In this case the nested function presents the dialog to the user, and then optionally shows another dialog which indicates the result. You could have just as easily changed state on some object, or signaled a different thread, with the outcome of the question, depending upon your needs.

Exercise for the reader: did you notice anything we forgot to make translatable in the above code?

### Settings Dialogs And Panels

#### Introduction

As noted above, dialogs are useful in allowing users to interact with add-on features. One variation of a dialog is a settings dialog where users can configure add-on features themselves.

Settings dialogs can be done in two ways: dedicated settings dialog, or as a panel in NVDA Settings dialog. A dedicated settings dialog is useful if settings are divided into sections, such as dedicated panels of their own. In contrast, settings panels are used to integrate add-on settings as though they are part of NVDA settings.

Prior to NVDA 2018.2, only a dedicated settings dialog was supported. NVDA 2018.2 introduced settings panel for use by add-ons. This guide will discuss settings panels exclusively since dedicated settings dialogs are variation of interactive dialogs (see above for details).

#### Settings Panel Ingredients

To create settings panels, you must come up with a way to store add-on settings and make them configurable. A common way to do this is include a configuration specification (confspec) which will be used to configure add-on options.

In addition to configuration specification, you must import NVDA GUI helpers, as well as define a class that inherits from gui.SettingsPanel class with the following defined:

- title (required): the name of the panel.
- makeSettings (required): a method to populate settings.
- onSave (required): react to OK button.
- isValid (optional): validate settings before saving.
- postSave (optional): take action after OK button is clicked.
- onDiscard (optional): respond to Cancel button being clicked.
Lastly, when the add-on is run, add the just define panel to NVDA settings panels list and remove it when the add-on is being terminated.

#### Example: A Basic Settings Panel

The below example is a global plugin with a settings panel with a simple checkbox.

    # A global plugin with a simple settings panel

    import globalPluginHandler
    import gui
    import wx

    sampleOption = False

    class OptionsPanel(gui.SettingsPanel):
    	title = _("Simple Settings")

    	def makeSettings(self, settingsSizer):
    		sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
    		self.OptionCheckBox = sHelper.addItem(
    			wx.CheckBox(self, label=_("A simple checkbox"))
    		)
    		self.OptionCheckBox.SetValue(sampleOption)

    	def onSave(self):
    		global sampleOption
    		sampleOption = self.optionCheckBox.IsChecked()

    class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    	def __init__(self):
    		super().__init__()
    		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(OptionsPanel)

    	def terminate(self):
    		super().terminate()
    		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(OptionsPanel)

### Threading

#### Introduction

If a routine in an add-on runs for a long time, NVDA would appear to freeze or stop responding altogether. This is where threads come in - running a long-running task with a different thread, allowing NVDA to remain responsive.

Although Python does support threads, it can run one thing at a time due to global interpreter lock (GIL). Thus, on computers with multiple processor cores, it is advised to use processes (via multiprocessing module) to allow Python interpreters to run on all cores. However, this workaround introduces latency and overhead, so for many scenarios, threads are preferred.

#### Threading scenarios

Threads are useful if

- You need to work on something while waiting for a result. For example, if a global plugin needs to access the internet for various tasks, a separate thread can be used for obtaining online information while NVDA is busy with something else. A module named concurrent.futures is designed to obtain results from background tasks via threads.
- Monitor things in the background without interrupting NVDA. For example, an overlay class defined in an app module can use a thread to announce screen information as it changes in the background.
- Run tasks periodically. For example, a speech synthesizer can use a timer thread to determine if a hardware synthesizer is ready or not.

#### Threading examples

All examples use threading module unless noted otherwise.

Download content from a website via a global plugin:

    import threading
    import urllib
    # Other parts of the global plugin.

    def downloadContent(address):
    	return urllib.urlopen(address)

    class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    	def script_downloadContent(self, gesture):
    		downloadThread = threading.Thread(target=downloadContent, args=(someWebsite,))
    		downloadThread.start()
    		downloadThread.join()

We need to use a separate thread to access web content because urllib (urllib.request in Python 3) blocks, making NVDA appear to freeze.

Announce a message ten seconds after pressing a key from an app:

There are two timers you can use: threading.Timer or wx.Timer. The below app module example uses threading.Timer.

    import threading
    import ui
    # Other parts of an app module.

    class AppModule(appModuleHandler.AppModule):

    	def script_saySomething(self, gesture):
    		messageTimer = threading.Timer(10.0, ui.message, args=("this is a timer message", ))
    		messageTimer.start()

One limitation with threading.Timer is that it does not support repetitive tasks, and for these, you need to use wx.Timer.

### Using external Python modules

While NVDA uses many Python libraries (standard library and third-party modules), not all modules from Python standard library are available. Among these are parts of concurrent.futures, parts of multiprocessing module facility, and parts of XML modules (note that multiprocessing module cannot be used in NVDA).

In addition to modules from the standard library, Python can be enriched with third-party modules from sources such as Python Package Index (PyPI). These external modules allow programs to access web services and databases, read and parse thousands of file formats, improve programmer productivity such as error checking modules, and other functionality. Examples of third-party packages include requests, psutil, pillow, and markdown.

To include additional Python modules in an add-on, the contents of the module must be copied to the add-on source directory. Instead of a single app module or a global plugin module, a folder must be created to house an init.py to store your code as well as folders for external libraries you wish to use. For example, to use psutil to obtain information such as network statistics from a global plugin, create a folder with the same name as the global plugin name you are using, put an init.py file to store your global plugin code, download psutil from PyPI, then copy the psutil folder from Python installation directory (under lib/site-packages folder) to the global plugin directory you've created. Then from init.py file, import psutil (see below for possible ways).

You can import external modules in a number of ways:

- Relative import: the benefit of this method is that additional modules will be limited in scope to your add-on.
- Path manipulation: any modules loaded with this method will be visible throughout NVDA namespace.
For example, to use psutil (available from PyPI) in NVDA 2024.1 or earlier (psutil is part of NVDA 2024.2), provided that the psutil folder was copied to a folder underneath global plugins directory, you can use either method such as relative import from your module where psutil is going to be used:

    from . import psutil

Or load it after manipulating load paths:

    import sys
    sys.path.append(os.path.dirname(__file__))
    import psutil
    sys.path.remove(os.path.dirname(__file__))

Sometimes using relative imports will cause Python to raise "module not found" error if parts of the external library import a namespace package. If this happens, use path manipulation to import the external library. The latter is useful if you need to include modules from Python standard library not included with NVDA (for example, xml.sax).

### Using The Log

There are more in-depth things you can do with the log than what will be shown here. However, most of the time, all you want to do is write a basic message to the log. To do that, you can import NVDA's log singleton, and call its methods just like any others.

    import globalPluginHandler
    from scriptHandler import script
    from logHandler import log  # This is what you need for logging
    from datetime import date

    class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    	@script(
    		gesture="kb:nvda+shift+l",  # Configure the key
    		description="Run an add-on guide example"  # NVDA input help
    	)
    	def script_captainsLog(self, gesture):
    		today = date.today().strftime("%Y.%m.%d")
    		log.info(f"NVDA log. Earth date, {today}.")
    		log.warning("These are the add-ons of the screen reader NVDA.")
    		log.debugWarning("Its continuing mission. To seek out new opportunities to improve lives!")
    		log.debug("To empower users!")
    		log.error("and to boldly access software that no screen reader has made accessible before!")

If you run the above in the NVDA scratchpad or a global plugin, and call it by pressing the Shift+NVDA+L key sequence, you will receive between zero and five log entries, depending on how your NVDA logging level is configured in general settings. For example, if your log level is set to "debug", you will find them all there, but only four of them if your log level is set to "debug warning".

Note: while developing add-ons, it is usually wise to have the most debugging that you can, so you can gather information when things go wrong. For that reason, you may want to set your logging level to "debug".

## The add-on development guide: Appendices

### Appendix A: add-on terms dictionary

The below terms are used throughout this development guide as well as in the add-ons community to refer to add-ons, development processes and so on.

- Add-on: an extension for a program. In NVDA world, add-ons refer to additional packages users can install to extend NVDA's functionality, improve support for an app, or add new speech synthesizers or braille displays.
- Application: synonymous with program.
- App module: a module that adds or improves support for a program.
- API: Application Programming Interface.
- Base class: parent class of an object.
- Braille display: a hardware or software that outputs text via tactile braille output and/or allows users to enter text via a braille keyboard or other input mechanisms.
- Built-in module: a module that comes with NVDA that add-ons can optionally override or extend.
- Caret: cursor shown on screen, usually seen when editing text or navigating documents.
- Class: definition of an object.
- Driver: a program that allows another program to talk to other software or hardware.
- Enhancer: a module that adds usability enhancements in tandem with NVDA.
- Event: a routine called when certain things happen such as character input, changes to text on screen, a checkbox being checked and so on.
- Function: a piece of code that performs something given one or more input parameters and optionally returns something.
- Gesture: a piece of input such as key presses, touchscreen flicks, braille keys and so on.
- Global plugin: a module that adds features everywhere.
- Module: collection of variables, functions, classes and others inside a file.
- Object: a class definition coming to life.
- Script: a function that is attached (assigned) to a gesture.
- Speech synthesizer: a software or hardware that converts text and various speech commands sent to it into voice output.
- Variable: a temporary placeholder for some data.

### Appendix B: Programming and Python concepts every add-on developer needs to know

The below list summarizes concepts all add-on developers will need to know when writing add-ons.

- API: a set of documentation and code samples used to let a program or hardware interface with other software or hardware.
- Base class: a class that provides base methods, attributes and properties for other objects to inherit and extend. Synonymous with superclass and parent class.
- Child class: a class that derives its power from one or more base classes.
- Class: definition of objects, including methods, attributes and expected behaviors. All Python classes and attributes are public; they can "become private" through use of naming conventions such as prefixing a variable name with underscores (_).
- Code block: collection of code.
- Compiling: translating a high-level programming language into a low-level language suitable for machine execution.
- Event-driven programming: a programming paradigm based on following, reacting to and handling events.
- Exception: one or more runtime circumstances that prevent normal operation of a program such as being denied access to a resource, name usage problem in code and other cases.
- GUI: Graphical User Interface.
- Handle: an opaque reference to a resource such as a file, TCP socket, window and so on.
- Has versus is relationship: former referring to attributes of a single class, the latter referring to inherited classes.
- Indentation-based syntax: use of indentations such as tabs to denote code blocks.
- Inheritance: ability for one or more parent classes to provide base methods and attributes for child classes to override or extend as the need arises.
- Interpreting: running a program written in a high-level language without compiling it first.
- Object: runtime instance of one or more classes.
- Object hierarchy: how screen elements are organized via parent-child (container-contained) relationship.
- Object-oriented programming: a programming paradigm that defines solutions to problems or represent real-life things via classes and objects.
- Scope: where variables, functions, classes and objects are defined in code.

### Appendix C: Add-on type comparison

The following table compares various add-on types and when to use them.

Task or feature

Global plugin

App module

Driver

Enhancer

Can be used everywhere

Yes

No

Yes

Yes

Naming restrictions

No (limited by Windows file naming conventions)

Must be name of the executable

No (limited by Windows file naming conventions)

No (limited by Windows file naming conventions)

Retrieve various controls, including focused control

Yes

Yes

No

Yes

Commands can be used everywhere

Yes

No

Braille display drivers only if defined

Yes

Handle events such as focus changes

Yes

Yes

No

Yes

Define custom objects to represent controls

Yes

Yes

No

No

Define custom actions to be performed when the module loads and unloads

Yes

Yes

Yes

Yes

Perform actions when profile switching occurs and other actions

Yes

Yes

Yes

Yes

Can modify object attributes at runtime

No

Yes

No

No

Modify speech and other output routines and presentation experience (i.e. speech.cancelSpeech, braille.handler.update, etc.)

Yes

yes

No

Depends on enhancer

Include custom settings

Yes

Yes

Yes

Yes

Can patch NVDA functions, classes and modules at will

Yes

Not advised

No

Not advised

Subject to configuration profile switches

No

Yes

Yes

Yes

Can call external libraries written in C and other languages and bundled as DLLs

Yes

Yes

Yes

Yes

### Appendix D: notes and references for scripters of other screen readers

If you write scripts for screen readers such as JAWS for Windows or Window-Eyes, be sure to go over this section as it introduces you to common tasks you can do with NVDA and other notes.

Task

NVDA or Python function/class/module

Notes

Cancel speech

speech.cancelSpeech()

Stops speech.

Speak something

speech.speakMessage(message) or as part of ui.message(message)

the ui.message function also performs braille output.

Braille something

braille.handler.message(message) or ui.message(message)

Same as above.

Show an HTML window

ui.browseableMessage(message, title, isHTML = True)

Mimics virtual viewer except it'll be shown on screen.

Retrieve focused object

something = api.getFocusObject()

Retrieve foreground window

foreground = api.getForegroundObject()

Title of the active window (if present)

foreground.name

Find out what object is navigator object

obj = api.getNavigatorObject()

This may or may not be the focused control.

Retrieve window handle for a given object

hwnd = obj.windowHandle

Obtain object via api.get*Object() functions.

Check the name of the window class

obj.windowClassName == somename

Making sure the parent object has the correct window control ID

if obj.parent.windowControlID == something: statement

The parent object does not provide what I want, but the grandparent does

something = obj.parent.parent.attribute

The label of a list item is the name of its first child object

obj.name = obj.firstChild.name

I want the control label of the focused object and description of the previous object to be announced when I press NVDA+Tab

In reportFocus(self): obj.name += " " + obj.previous.description

Announce state changes if and only if the next object is the toolbar I'm looking for

In event_stateChange(self): toolbar = obj.next; if toolbar.role == controlTypes.Role.TOOLBAR and toolbar.attribute = whatYouAreLookingFor and additional conditions ...: statement

For better readability, place each statement on separate lines with correct indents applied.

Announcing the name of an object on screen (provided that object navigation can be used)

obj = api.getForegroundObject().route...; ui.message(obj.name)

Try placing each statement on its own line with correct indents applied. Route refers to obj.next/previous/parent/firstChild/lastChild/children[index]/getChild(index) and so on.

Check if the object's role is what you want

obj.role == controlTypes.Role.*

Role.* can be any role you are looking for.

Looking for a specific text in the object's name

sometext in obj.name

This is a typical string membership task.

Does the control's label start with a specific text

obj.name.startswith(sometext)

Length of a text field with easily retrievable value

len(obj.value)

This works if the value of the field can be found.

Is a checkbox checked

controlTypes.State.CHECKED in obj.states

obj.states is a set. First, verify that the role is a checkbox.

How many items are in a list

someList.childCount

Provided that the list provides correct underlying implementation to obtain item count.

Where the object is located on screen

obj.location

This returns a tuple of four elements, namely x and y coordinates of the top-left corner of the object, as well as length and width. For example, on the Shell (desktop) object with screen resolution of 1920 by 1080 pixels, the return value will be (0, 0, 1920, 1080.

Is this an MSAA control

isinstance(obj, NVDAObjects.IAccessible.IAccessible)

A typical implementation is to import IAccessible from NVDAObjects.IAccessible and doing isinstance(obj, IAccessible).

Position of a MSAA list item

item.IAccessibleChildID

Provided that this is properly implemented. The default for controls other than list items, treeview items and what not is 0.

I need to work with IAccessible object methods directly

obj.IAccessibleObject.method

First, find out how to use the given MSAA method for a control, then retrieve the IAccessible object itself and call the needed method.

Give me the UIA element that powers a certain UIA control

obj.UIAElement

Useful if you wish to perform UIA client operations on this element.

Automation ID for a UIA element

obj.UIAAutomationID

First, check if the object is a UIA control.

Framework used to generate this UIA object

obj.UIAElement.cachedFrameworkID

The GUI framework used to program this object. Commonly encountered frameworks are Direct UI, Windows Presentation Foundation (WPF) controls with UIA enabled, XAML (eXtensible Application Markup Language) and Microsoft Edge.

I want to ask UIA about values of a specific property

obj._getUIACacheablePropertyValue(propertyID)

Provided that the object is a UIA control, pass in the property ID you wish to know as an argument to this function. If the property is supported, a valid value will be returned, otherwise a COM error exception will be thrown.

Executable name of any object

obj.appModule.appName

appModule is the attribute of any object that can be represented within an app such as focused control.

Path to the executable for the foreground object

api.getForegroundObject().appModule.appPath

Obtains the path to the executable for any object.

Provide information about a script in one go

scriptHandler.script(description, one or more gestures, category)

This is a decorator. Typically, you would write: @scriptHandler.script followed by the script information. Gestures can be a single gesture (gesture=string) or a list (gestures=[gestures]).

Assign a keyboard command to a script

@scriptHandler.script(gesture=keyboardCommand)

Keyboard gestures start with a "kb:".

Send keystrokes

gesture.send()

This is to be called from a script with the desired keystroke bound to it.

Handling multiple presses of a keystroke

scriptHandler.getLastScriptRepeatCount()

0 means the command was pressed once.

I want to assign Control+Alt+number row to a script

@scriptHandler.script(gestures=[f"kb:control+alt+{i}" for i in range(10)])

This uses a combination of a decorator and formatted string literals (f strings) defined inside a list comprehension.

providing input help message

@scriptHandler.script(description=inputHelpMessage)

Effectively, a script's description (assigned to its docstring) is treated as its input help message.

Speech on demand

@scriptHandler.script(speakOnDemand=True)

This argument is not included by default but can be set to True if you wish to announce information while the user is using the add-on and NVDA is set to speech on demand mode.

Handle name changes

event_nameChange(self, obj, nextHandler)

The body should consist of what should be done, ending with a call -to nextHandler() function.

Live region change announcements

event_liveRegionChange(self, obj, nextHandler)

By default, new text will be spoken and/or brailled.

Instantly transform a window into a dialog

In chooseNVDAObjectOverlayClasses(self, obj, clsList): if you found the window you want: clsList.insert(0, NVDAObjects.Behaviors.Dialog)

Be sure to identify this window that is really a dialog. If done correctly, contents of this "dialog" will be announced automatically.

I'm working with a terminal window

Inherit from NVDAObjects.behaviors.Terminal

I want to add table navigation commands for an object that is not shown as a table yet

Inherit from NVDAObjects.behaviors.RowWithFakeNavigation

This class defines input help mode message and a base implementation for table navigation commands (Control+Alt+arrows).

I need pointers for providing improved support for a Java application

NVDAObjects.JAB and JABHandler module

Java Access Bridge (32-bit and 64-bit) should be installed (installed in 2019.3).

Adding support for an app that has similar functionality as another app

Import contents of the source app module via from appModuleName import *

Commonly called "aliasing".

Play a tone

tones.beep(hertz, duration)

Duration in milliseconds.

Play a tone on the left speaker

tones.beep(hertz, duration, leftVolume=100, rightVolume=0)

Play a wave file

nvwave.playWaveFile(path)

For example, nvwave.playWaveFile(r"test.wav")

Obtain text info for a given object

obj.TextInfo

Note the uppercase "T".

Check if keyboard echo (typed characters) is on

config.conf["keyboard"]["speakTypedCharacters"]

turn speak command keys on without opening a settings dialog

config.conf["keyboard"]["speakCommandKeys"] = True

The user should toggle this on via keyboard settings dialog.

Is focus mode/forms mode active

obj.treeInterceptor.passThrough

If True, focus/forms mode is on while using browse mode documents.

Is touchscreen support available

touchHandler.touchSupported()

If true, touch support is active and available.

Get NVDA version

buildVersion.version

I wish to do something whenever configuration profiles are changed

config.post_configProfileSwitch

You need to register a function to listen to this action, then let this function do something when profiles are changed.

Let me know if this is a snapshot build

debug

If yes (True), this is a snapshot build, otherwise this is a release version.

I need certain features in order for my code to work better

hasattr(module, something)

This allows you to check for existence of a feature/attribute you need, as it then allows you to support old and new code paths.

Windows version

winVersion.getWinVer()

This returns current Windows version (Windows release name, major.minor.build, installation type (workstation, server, domain controller), and service pack if any). You can also compare the version returned against a specific Windows release from winVersion module e.g. winVersion.getWinVer() >= winVersion.WIN81.

Is 64-bit Windows

winVersion.getWinVer().processorArchitecture in ("AMD64", "ARM64")

Both AMD64 and ARM64 must be checked especially when supporting Windows 10 or 11 on ARM.

Registry access

winreg module

Open a website with the default web browser

os.startfile(URL)

Download headers for a file on the web

resource = urllib.urlopen(URL)

Work with JSON data

json module

Allocate some memory somewhere

ctypes.windll.kernel32.VirtualAllocEx()

The faster way to do this is winKernel.virtualAllocEx function.

Send a message to another process

ctypes.windll.user32.SendMessageW()

The shorter way is winUser.sendMessage() function.

Current time in seconds

time.time()

This returns seconds elapsed from January 1, 1970 at midnight.

Create a message box

gui.messageBox

A thin wrapper around wx.MessageBox class.

Create a custom dialog

wx.Dialog

Run multiple background tasks at once

threading.Thread

In reality, due to internal issues, Python will run one thread after another. This approach is useful if you want to run a background task while making NVDA remain responsive.

Run something periodically

wx.PyTimer or threading.Timer

Tally occurrence of text in a document

collections.Counter

Be sure to have a list of words from a text file before running a tally on it.

Create a dynamic array

list object

Python's list object ([]) is a dynamic array.

Work with associative arrays

dict object

Python's dictionary ({}) object is another name for associative array, sometimes called a map.

Open, parse, and save config files

config module or configobj module

I wish to make my code run faster and error-free

DO NOT DO IT UNLESS YOU REALLY NEED TO!

To paraphrase a quote from a famous programmer, "don't optimize unless you want to go through headaches".

I want to release version 1.0 of my code with everything included

NEVER DO THAT UNLESS YOU KNOW WHY, know WHAT YOU ARE DOING, OR SPECIFIED BY A CONTRACT YOU SIGNED!

I wish to bring a feature from another screen reader to NVDA

Justify why and plan accordingly

I want to contribute features of my add-on to NVDA screen reader

Send in a pull request and prepare to answer questions from reviewers

Sometimes, a feature or two from an add-on do land in NVDA screen reader but after going through pull request review process. For more information, see NV Access's contributing guidelines.

## The add-on development guide: Audience

### Add-on distribution process for NV Access add-on Store

NVDA includes a built-in add-on store to browse, install, update, and remove add-ons. While you can publish your add-ons from the place of your choosing (GitHub, custom website), NVDA community recommends using the add-on store when publishing add-ons. Details are provided toward the end of this guide.

### Audience

This guide is designed for:

- Python beginners
- People new to NVDA development
- Expert Python developers
- Expert NVDA developers
- People familiar with programming languages other than Python.
- Developers of scripts for other screen readers.
If you are new to NVDA add-on or core development, we recommend that you get to know [Python](https://python.org) first, as it gives the necessary programming background for understanding the rest of the guide. If you are a Python programmer but new to NVDA development, please review the [NVDA Developer Guide](https://www.nvaccess.org/files/nvda/documentation/developerGuide.html) and [Design Overview](https://github.com/nvaccess/nvda/wiki/DesignOverview) document.

### A special note about Windows Store version of NVDA

As of NVDA 2018.1, foundation has been laid to let NVDA run as a Windows Store application. Once the Windows Store version of NVDA is published to Microsoft Store, users running Windows 10 can go to Store and obtain NVDA. However, there are restrictions that come with this version of NVDA, notably add-ons cannot run in this environment. Thus, if you need to run or write NVDA add-ons, you need to use the classic desktop version of NVDA, available from the [nvaccess.org website](https://www.nvaccess.org/).

### A special note for scripters of other screen readers

Some of the concepts described in this document are the same across different screen readers, such as objects, windows, events, accessibility API and so on. However, there are important things to be aware of when writing or porting scripts:

- Unlike some screen readers, NVDA does not have a formal specification or an object model as defined by documentation in other screen readers.
- The code you write will run inside the same runtime environment as the screen reader itself. Therefore, you can perform things such as obtain focused object directly, modify NVDA's functionality and even replace NVDA functions and classes with your own.
- Python, and consequently, NVDA is an object-oriented system. In other words, most of your code will consist of defining classes and objects which are then picked up by NVDA at runtime.
- Unlike scripting engines for some screen readers, there is no special hack involved when you wish to provide a feature that'll work in all applications.
- Unlike scripting engines for some screen readers, you are not limited to libraries that come with screen readers; as a Python-based program, you can use any python module(s) that fits your needs, including external modules. For example, a popular module used to interface with web applications is JSON (JavaScript Object Notation) module, which isn't bundled with NVDA versions prior to 2017.3. You need to bundle external Python libraries yourself if you choose to use these packages.

### Special note on 64-bit NVDA

Initially, NVDA was a 32-bit screen reader utilizing 32-bit x86 Python runtime. Throughout 2025, NV Access and contributors worked on 64-bit transition. As of December 2025, 64-bit transition is ongoing with add-on compatibility testing as alpha snapshots are 64-bit builds.

### Special note on NVDA backward compatibility

To modernize NVDA source code and to respond to screen reader usage changes, NV Access has adopted an annual backward compatibility policy in 2020. For each calendar year, the first major version (year.1) is designated "backwards incompatible" release where changes affecting add-ons will be incorporated. These include changes to names of functions and classes, as well as removing deprecated code. Because these changes will affect many add-ons, developers must test their add-ons for compatibility once the first beta of the backwards incompatible version of NVDA is released.

List of backwards incompatible NVDA releases and their highlights:

- 2019.3: Python 3
- 2021.1: dependency updates
- 2022.1: control types refactor
- 2023.1: new extension points
- 2024.1: Python 3.11 upgrade, speech on demand mode for scripts
- 2025.1: Windows Audio Session (WAS) API replaces WinMM for audio output, GUI MessageDialog API, remote access feature
- 2026.1: Python 3.13 upgrade, 64-bit transition
Unless otherwise stated, this guide will assume latest backwards incompatible NVDA when giving code examples (as of December 2025, 2026.1 is assumed with notes from upcoming releases). Exceptions will be documented in appropriate places.

### Special note on Python version

Until 2019, NVDA and add-ons were written primarily in Python 2, specifically 2.7. As of July 2019, NVDA was transitioned to use Python 3.7, with some add-on developers modifying their add-on source code to run on Python 2 and 3. With the release of NVDA 2019.3 in February 2020, Python 3 transition is complete, and from January 2022, Python 3 is required.

Subsequently, NVDA was upgraded to:

- Python 3.11: NVDA 2024.1 (early 2024)
- Python 3.13: NVDA 2026.1 (in development)
Be sure to keep an eye on NVDA development and add-ons mailing lists, as well as relevant development documentation and notices regarding news on Python 3 and NVDA. This guide will use strictly Python 3 code.

### A very important note about control types module changes in NVDA 2021.2

NVDA 2021.2 introduces control types refactor that changes how control roles and states are specified. In older NVDA releases, control roles are written as controlTypes.ROLE_, and states are written as controlTypes.STATE_. With control types refactor, roles and states must be written as controlTypes.Role.* and controlTypes.State.*, respectively. For example:

- Editable text role:
    - 2021.1 and earlier: controlTypes.ROLE_EDITABLETEXT
    - 2021.2 and later: controlTypes.Role.EDITABLETEXT
- Checkable state:
    - 2021.1 and earlier: controlTypes.STATE_CHECKABLE
    - 2021.2 and later: controlTypes.State.CHECKABLE
The older way of specifying control roles and states is deprecated in NVDA 2022.1 and kept for compatibility. Unless otherwise stated, this guide will use the newer style.

### A very important note about migrating custom extension code to development scratchpad

If you are coming from NVDA 2018.4 or earlier, you may recall that you are able to run extension modules (sometimes called "plugins") inside folders stored in the user configuration directory (e.g. appModules). This functionality has been revised in NVDA 2019.1 as follows:

- NVDA will no longer load extension code stored in the following subdirectories of the user configuration folder: appModules, brailleDisplayDrivers, globalPlugins, synthDrivers.
    - If you find that code inside these folders is no longer working as of NVDA 2019.1, the above reason is why.
- You must enable development scratchpad functionality (reserved for developers) if you wish to load custom extension code. To do so:
    - With NVDA 2019.1 (or later) running, go to NVDA menu/Preferences/settings/Advanced.
    - You must check "I understand that changing these settings may cause NVDA to function incorrectly" checkbox.
    - You must check "Enable loading custom code from Developer Scratchpad directory" checkbox.
    - Select OK.
- You must store code that was formerly housed in the above list of subdirectories inside corresponding subdirectories of the scratchpad folder.
- If you need to use NVDA 2018.4 and would like to use custom code, you must not remove the above listed subdirectories from the user configuration directory. Otherwise go ahead and remove the folders listed in item 1.

## The add-on development guide: Drivers

### Driver components

All drivers (regardless of target device or software to be supported) import appropriate modules such as `synthDriverHandler`. For most drivers, majority of the driver code deals with communicating with the target device or software, and all drivers must define the driver class (synthDriverHandler.SynthDriver or braille.BrailleDisplayDriver).

All driver classes, at a minimum, must include:

- Driver identifier: a camel-case string such as "oneCore" that uniquely identifies a given driver.
- Friendly name: the name that'll appear under synthesizer or braille settings dialogs.
- Availability flag: a class method named `check` that tells NVDA that the driver is ready for use.
- Connection manager: a set of routines that instructs NVDA as to how to locate a given synthesizer or a braille display.
- Output handler: a function that'll perform the actual output processing. For synthesizers, `speak` method must be present; for braille displays, `display` method is needed.
For speech synthesizers, they need to have:

- Synth settings ring options: a list of synthesizer settings users can adjust via synth settings ring.
For braille displays:

- Input handlers: if input from the braille display is desirable, the driver author must implement responders for commands such as braille keys, routing buttons and additional hardware.
- Command set: a map that identifies NVDA command assignments for various display hardware buttons.

### Drivers

A driver allows software such as NVDA to communicate with hardware or use functionality provided by another software. Typically, when people speak of drivers, they usually refer to a program installed on a computer that allows software to communicate with a specific piece of hardware, such as video cards, keyboards and so on.

In NVDA, drivers refer to modules that NVDA can use to communicate with a speech synthesizer or a braille display. For instance, you can write a braille display driver that sends braille output to your braille display, or ask your synthesizer to switch languages and provide configurable settings.

### A Few important things to remember before, during and after driver development

- Before writing a driver, make sure you have the actual software and/or hardware.
- Be sure to study protocols and APIs used by a speech synthesizer or a braille display (this is more so for braille displays which may implement different protocols).
- Make sure you know how to communicate with your equipment or software - ports, USB IDs, Bluetooth addresses, serial port settings, DLLs and so on.
- Work with another person who happens to use the equipment or software you are writing driver(s) for.

### Typical driver development steps

When writing drivers, you may wish to follow the recommended steps for app module development (planning, talking to vendors, user test, etc.). However, since drivers require intimate knowledge of hardware and/or software, you should spend more time testing your driver. This is more so if you are writing a driver for a braille display which can send arbitrary commands (braille commands, routing buttons, etc.).

## The add-on development guide: Enhancers

### Enhancer components

An enhancer such as vision enhancement provider will look similar to a combination of a global plugin and a driver (see above sections for explanations). For the most part, components used for drivers are applicable. These include:

- Enhancer identifier: a camel-case string such as "screenCurtain" that uniquely identifies this enhancer.
- Friendly name: the name that'll appear under Vision dialog.
- Supported enhancements: a frozen set of enhancement roles this provider will introduce.
- Startup check: a routine that will ensure NVDA is running in a specific environment where the enhancer would be most helpful, such as checking for a specific Windows release.
- Startup and shutdown: a class constructor that instructs the enhancer to come online and a "terminate" method that shuts it down.
- Event registrar: if an enhancer wishes to respond to various actions performed by users, it can specify follow-up actions.

### Enhancers

An enhancer is a module that helps certain groups of users use computers more efficiently. Enhancers may include cursor tracking, magnification, and other enhancements.

Currently NVDA can provide assistance through vision enhancement providers. A vision enhancement provider is an enhancer that allows people with low vision or sight use computers effectively by working in tandem with NVDA. Enhancements may include cursor highlighting, screen curtain effect, and magnifying parts of the screen. These enhancers are stored under "visionEnhancementProviders" folder and defined as a "VisionEnhancementProvider" class which inherits from "vision.providerBase.VisionEnhancementProvider".

Note: because only one enhancer is supported at this time, we will refer to vision enhancement provider in the sections below.

### A Few important things to remember before, during and after enhancer development

- Be sure to talk to users planning to use your enhancer. For vision enhancement providers, make sure the enhancements are indeed what users want.
- Test your enhancers with many users to make sure they are working correctly.

### Typical enhancer development steps

When writing enhancers such as vision enhancement providers, you may wish to follow the recommended steps for driver and global plugin development (planning, talking to users, user test, etc.). As these modules will affect NVDA experience globally (even when switching configuration profiles), make sure the enhancer does not degrade user experience for people not needing it.

## The add-on development guide: Getting started: Hands-on examples

### Example 1 code explanation

Our first example lets us sound a beep for one second when we press NVDA+A. But you might be wondering what that above code means, so let's step through the code, one piece at a time.

- At the top of the file, we wrote a header which tells us that this is an example add-on.
- Since this is a global plugin, we need to import a crucial module: global plugin handler, so we wrote `import globalPluginHandler`.
- Then we wrote `import tones` to import (load, or include) the tones module, a built-in module from NVDA. Whenever you wish to use a method from a given module, import the needed module(s).
- Next, we defined a class called GlobalPlugin. The text inside the brackets tells us where this class is coming from (more on this concept in a second). A class, in programming, describes an object, such as a person, a desk, a program and others.
- Inside the class, we wrote a method (function) called `script_doBeep`. This is an example of a script, a method that'll be run or executed when you press a command. Inside this script, we wrote `tones.beep(440, 1000)` to tell NVDA to sound a middle A tone for 1 second. In programming, a function can take arguments, or a set of parameters which tells the function what to do based on the given values (we'll meet them later). In fact, many methods you'll be writing, including our doBeep script takes one or more arguments. More on scripts later as we journey through the guide.
- Lastly, we wrote a simple dictionary (a collection) to store our command (script) bindings for our doBeep script. Here, we told NVDA to assign NVDA+A command for doBeep script. Later you will learn a handy trick that will let you specify script bindings and other information at the same time as the script itself.
Save this file, then restart NVDA. Now whenever you press NVDA+A, you'll hear a middle A tone for 1 second. Once you are comfortable with the add-on code and how it is laid out, you can delete the newly created .py file.

### Example 1: Hear a tone when pressing NVDA+A

Let us start with a simple example: if you press NVDA+A, you will hear a tone for 1 second in any program. Since we want to use this everywhere, it must be a global plugin.

First, if you haven't done so, enable development scratchpad. Then open your user configuration folder, then open the scratchpad folder (if it exists--create it if not), then select globalPlugins folder. Create a new .py file and give it a descriptive name such as example1.py (it is strongly recommended that when you name your global plugin file, give it a short descriptive name). Then open the newly created .py file in the word processor.

The following code implements our example. Put this in your .py file as exactly as shown:

    # Add-on development first example

    import globalPluginHandler
    import tones # We want to hear beeps.

    class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    	def script_doBeep(self, gesture):
    		tones.beep(440, 1000)  # Beep a standard middle A for 1 second.

    	__gestures={
    		"kb:NVDA+A": "doBeep"
    	}

In Python, you make comments by putting hash sign (#) at the start of the comment line.

### Example 2 code explanation

We're seeing more new code here. Let's go over this, again piece by piece:

- Unlike the first example, the crucial module we need is appModuleHandler.
- The class that we are using is AppModule.
- Unlike last time, we're using events, a method run when certain events occur such as when names of controls change. Events take an object as one of its arguments, the object for which the event needs to be dealt with, or, as many people say, "fired."
- Inside the event method, we're also seeing a call to `nextHandler`. This method is used in event methods to tell NVDA to pass the event so it can be taken care of, such as saying the name of a control after beeping.

### Example 2: Generate a tone when switching to Notepad

Most of the following code comes from NVDA Developer Guide.

NVDA doesn't just let you add global commands, but it also allows writing code to enhance usage of programs through app modules. An app module is also a Python file except that, this time, the name of the .py file is the name of the executable for a program. For example, an app module for Notepad would be named notepad.py.

The following code, from NVDA developer Guide, gives a short example of a typical app module: play a short beep when switching to Notepad. Put the following code in notepad.py, which in turn should be placed in appModules folder under scratchpad directory (if enabled) in your user configuration folder in order for it to run.

    # An example app module.

    import appModuleHandler
    import tones

    class AppModule(appModuleHandler.AppModule):

    	def event_gainFocus(self, obj, nextHandler):
    		tones.beep(256, 200)
    		nextHandler()

### A few tips for beginners

Here are a few useful tips passed on by add-on writers:

- Start with easy add-ons, such as saying a message, tones and so on.
- Write and test one method at a time.
- If you are writing app modules or drivers, become familiar with programs, synthesizers or braille displays you wish to support (e.g. read the documentation, try using them, etc.).
- When defining commands (especially in global plugins), consult commands used in NVDA and other add-ons first before assigning a new command in your add-on to avoid command conflicts.

### Getting started: Hands-on examples

So, are you ready to start your adventure with add-ons, but not sure as to how to bring it to life? If that is you, please go through this chapter, as it gives you basic information to get you started with add-ons and give you tips on writing code.

Note: for this chapter, we will not use the actual add-on packages. Instead, we'll use scratchpad plugin folders - a number of subdirectories located in a folder called "scratchpad", which in turn is a subfolder of your NVDA user configuration folder (available from Start Menu/Screen if NVDA is installed) to store our example Python files.

IMPORTANT: this chapter covers Python modules (global plugins, app modules, drivers, vision enhancement providers). Custom braille tables and speech symbol dictionaries will be covered later in this guide.

To edit .py files, you need a word processor which can handle .py files. The best one we recommend is Notepad++.

### How add-on code is organized

Your add-on code is stored in one or more Python files (.py file). Despite different kinds of add-ons out there, they all have similar layout.

First, you start by writing an optional header for your add-on, such as your name, a brief sentence or two on what the add-on is for and so on. Although this is optional, it is recommended that you write the header as a reminder to keep track of what you are doing with your add-on. If you plan to distribute your add-on, you must write a header with copyright and license notices.

Next, you tell NVDA the modules you need for your add-on file. This is done by writing `import module` where module is the name of the module you wish to use in your code. For example, if you want to hear tones while writing your add-on, write `import tones`. Typically, you may need to import two or more modules for your specific add-on (see below on list of modules you need for the type of add-on module you are writing).

after declaring the modules you need or import, you write your add-on code (defining classes, variables, methods and so on). The most important section is the add-on class code, which will determine the type of add-on module your code will be assigned to.

For instance, if you wish to add support for a program, after importing appModuleHandler and other needed modules, you will write:

`class appModule(appModuleHandler.AppModule):`

After that, all you are writing is Python code (see the Python documentation on how to write Python programs).

### I don't understand those above terms

For some, the terms "class", "method" and so on might be new. Let's go over what these terms are, as they are fundamental for add-on development:

- Class: a class describes an object. It could describe anything, such as a person, a desk, an NVDA add-on and others. Classes are fundamental to NVDA and other programs - in fact, a number of programmers are skilled at coming up with classes.
- Method: A method is a short program or a routine that a program runs for doing something, such as generating tones, calculating huge numbers, loading NVDA add-ons and so on. Some people call them "functions."
- Script: A script is a method which runs when the user performs commands such as pressing certain keys on a keyboard. For example, when you press NVDA+F12, NVDA runs dateTime script, located in one of the NVDA core modules named Global Commands. A script takes two arguments: where the script would be executed (usually "self"; more on that later) and the gesture for the script (see below).
- Variable: A variable is something that can change, such as name of a person, name of the NVDA add-on we're running, version of NVDA you are using and so on. An add-on file may define one or more variables (for example, to store common constants such as strings).
- Module: A module is a collection of methods and variables in a file. When we write add-ons, we are in fact writing additional modules that NVDA can use while it is running.
There are other terms that we'll get to know shortly.

### More new terms please

Other terms you may see include:

- Event: An event is a method that'll be run when something occurs, such as when a program is focused, when names of controls change and so on.
- Call: We say a function or method "calls" another method when we run the second method from the first method. Our first example above demonstrates this, by calling the tones.beep method from our script method.
- Object: An object is an instance of a class - that is, a class coming to life when a program runs. Throughout your add-ons, as you write classes and when you run your add-ons, your classes come to life as objects (commonly abbreviated to obj). In NVDA, an object may refer to controls or parts of a program.
- Self: In Python, the word "self" means current class (if we're defining one, such as when writing add-ons), or means the class for which a method is defined. For example, in a class called numbers, the "add" method would have self as the first argument, reminding us that add method is part of the class of numbers. In NVDA development world, self usually means the current NVDA object (see below), or in the add-on development, the instance of an add-on. Many of your methods will have self as the first argument.
Just like example 1, once you're comfortable with app module code, you may wish to delete the Notepad app module code unless you want to keep hearing beeps when you switch to Notepad. The actual differences between global plugins and app modules will become clearer when we talk about them in more detail throughout this guide.

### Running your add-on in this example chapter

Before you can run example add-ons, you must enable development scratchpad from NVDA's advanced settings. After doing so, a new folder named "scratchpad" will appear in user configuration folder. See the section on scratchpad above for details on how to do so.

To run your example add-ons from this chapter, open your NVDA user configuration directory (from Start Menu/Screen, look for Explore NVDA user configuration folder" item). Then look for "scratchpad" folder (if enabled), then paste your .py file to the appropriate folder inside this subfolder: appModules folder for app module examples, and globalPlugins folder for global plugins.

## The add-on development guide: Introduction to app modules

### App module development process and strategies

A typical app module is developed thus:

- You or a user requests enhanced support for a program.
- If possible, contact the app vendor (programmer) and request accessibility improvements for the program.
- With or without cooperation from app vendor, you would examine how the program works and areas on the screen that need to be read out.
- Write and test the app module (with users) until the app module is ready for release.
As you write app modules, try these tips:

- Use objects to represent parts of a program. This is done in two steps: define the control for parts of a program via objects (inheriting from some object such as IAccessible), then use `chooseNVDAObjectOverlayClasses` routine to tell NVDA to work with your custom object when working with that control. See overlay classes section for tips.
- If possible, test your app module using two or more versions of the program to make sure your app module works with those versions.
- You should not incorporate all desired features in version 1.0 - leave some of them for a future release.

### Differences between app modules and global plugins

At first glance, app modules may look the same as any global plugin. However, app modules have additional properties that global plugins lack, including:

- Instead of `globalPluginHandler`, you need to import `appModuleHandler`. The class to implement is `AppModule(appModuleHandler.AppModule)`.
- App modules are stored in appModules folder in your add-on directory structure and named the same as the executable name of the program.
- You can ask NVDA to enter sleep mode in a program where NVDA will not speak or braille anything while using the program, and any keyboard commands you press will be handled by the program directly. This is done by setting `sleepMode` attribute in the AppModule class to True.
- Some apps present information in the form of a webpage, and if this happens, browse mode can be used. However, in NVDA 2019.2 and later, this ability is disabled for apps such as Skype. To restore browse mode functionality, you need to set disableBrowseModeByDefault to False.
- The `event_NVDAObject_init` routine is only available in app modules.
- You can ask NVDA to keep an eye on an object to handle events for them even if the user is using another app.

### Example 1: Simple app module in Notepad

Suppose you wish to find out which line you're editing in Notepad. Assuming that Notepad will show status bar at all times, you wish to assign a key combination to read the current line number.

The app module for Notepad would look like this:

    # Example app module for Notepad, notepad.py.
    import appModuleHandler
    import api
    import ui
    from scriptHandler import script

    class AppModule(appModuleHandler.AppModule):

    	@script(gesture="kb:NVDA+S")
    	def script_sayLineNumber(self, gesture):
    		# Suppose line number is in the form "  ln 1".
    		lineNumList = api.getStatusBar().getChild(1).name.split()
    		lineNum = lineNumList[0]+lineNumList[1]
    		ui.message(lineNum)

So, whenever you run Notepad, when you press NVDA+S, NVDA will say line number.

### Example 2: Silencing NVDA in Openbook

Openbook is a scanning and reading program from Vispero (formerly Freedom scientific). Since Openbook provides speech, you can tell NVDA to enter sleep mode while Openbook (openbook.exe) is running using the below app module:

    # Silencing NVDA in openbook, openbook.py.
    import appModuleHandler

    class AppModule(appModuleHandler.AppModule):

    	sleepMode = True

With that single line of code, NVDA will enter sleep mode in that program (you should do this only if the program provides speech and/or braille support on its own).

### Example 3: Announcing control property changes while using another app

You can ask NVDA to handle specific events while it is focused on another app. This is done by calling eventHandler.requestEvents in app module's init method. In order to invoke this, you need process ID (PID) for the application, window class name for the object and the name of the event to be handled.

The following code allows NVDA to announce value changes while focused on another application.

    # Example app module for a messenger app.
    # The object we wish to track has window class name of "MessengerWindow".

    import appModuleHandler
    import eventHandler

    class AppModule(appModuleHandler.AppModule):

    	def __init__(self, *args, **kwargs):
    		super().__init__(*args, **kwargs)
    		eventHandler.requestEvents("valueChange", self.processID, "MessengerWindow")

Once defined, even if focused on another app, new messages (values) will be announced.

### Example 4: Customizing status bars as seen by NVDA

Typically, status bars are located at the bottom of the app window, but sometimes NVDA cannot locate status bars easily. You can customize status bar retrieval routine from an app module through a getter method (methods prefixed with "get").

The following app module tells NVDA that a UIA control with a unique Automation Id should be treated as a status bar.

    # Example app module for an audio editor.
    # The status bar cannot be retrieved using methods provided by NVDA.
    # However, a UIA element with a unique Automation Id shows status bar text.

    import appModuleHandler
    import api
    from NVDAObjects.UIA import UIA

    class AppModule(appModuleHandler.AppModule):

    	def _get_statusBar(self):
    		fg = api.getForegroundObject()
    		for element in fg.children:
    			if isinstance(element, UIA) and element.UIAAutomationId == "StatusBar":
    				return element
    		raise NotImplementedError

As long as this audio editor is in use, NVDA will use the status bar retrieval method defined in the app module to obtain status bar text.

### Introduction to app modules

An app module enhances support for a particular program. For example, you can write an app module which adds convenience commands for reading various parts of the screen, or you can define how a particular control should behave in a program.

An app module is a Python (.py) file with the name corresponding to the executable name of a program. For example, an app module for Winamp is named winamp.py since Winamp's executable name is winamp.exe.

NVDA itself comes with several app modules, such as Winamp, Adobe Reader, Microsoft Office programs and so on.

### Other remarks on app modules

- If you find that different versions of the program are laid out differently e.g. locations for controls are different, then you can write code which can handle these cases. There are a number of options you can choose from: adding some constants in your app module to handle different object locations, writing code for these controls (one per version) in custom objects which will be chosen in overlay class method and so on.
- If possible, try working with services that the app provides, such as COM (Component Object Model) methods (for example, Outlook app module), API's the app provides (such as Winamp) and so on.
- If you wish to extend an app module that comes with NVDA, use the following code fragment (this is called overriding the built-in module):
- `from nvdaBuiltin.appModules.appName import *`
- Where appName is the app module you wish to extend. For example, if you wish to support different controls in Windows calculator (calc.py), use:
- `from nvdaBuiltin.appModules.calc import *`\
- Many app modules (both built-in and third-party ones) use app names as part of the name for a constant (a value that doesn't change). For example, in NVDA's PowerPoint module (powerpnt.py), many constants start with "PP". Similarly, in Station Playlist Studio app module, many constants in the app module file (splstudio.py) start with "SPL". This is used to remind you where these constants are used.

### Supporting multiple apps with one app module

You can inform NVDA to use one app module to support multiple apps. For example, you can define an app module for a 32-bit version of a program and later reuse it to support 64-bit app version, or support a single app with changes to its executable name over time. NVDA ships examples of both cases.

Instead of writing multiple app modules with duplicated code, you can either alias a module by importing everything from one module to another or register the base app module for use when loading the derived app module. The below code is all that's needed to alias one app module from another (the code is placed in the alias/derived app module):

`from appName import *`\

Where appName is the name of the app module and * (asterisk or star) means import everything.

Alternatively, you can register an app alias but this involves bundling a global plugin with the registration happening as the plugin loads. The following code, a simplification of an actual add-on code, registers an alias of "app2" for "app1" to let app1 app module support app2 without duplicating the app module code:

    # App alias registration global plugin.

    import globalPluginHandler
    import appModuleHandler

    class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    	def __init__(self):
    		super().__init__()
    		# App2 is supported through App1 app module.
    		appModuleHandler.registerExecutableWithAppModule("app2", "app1")

This is one of a handful of cases where a global plugin must be bundled together with app module(s) to support apps.

### Useful app module properties and methods

`sleepMode` and `processID` are just two of many attributes that app modules have. Other useful properties and methods used in app modules include the following:

- appName: the name of the app (usually the name of the executable).
- productName: Records the actual product name for the app.
- productVersion: Records the version of the app.
- is64BitProcess: if true, the app is a 64-bit process (only true if you're using a 64-bit app under 64-bit Windows versions).
- dumpOnCrash: if you are debugging apps that crash often, you can call this function to let NVDA save a crash dump of this app in the temp files directory so you can retrieve it later.
- disableBrowseModeByDefault: some apps are essentially web documents, and as such, browse mode will be invoked. You must set this value to True if you want to force NVDA to treat this application as a proper application i.e. disable browse mode.
- appPath: records the path to the app executable.
- appArchitecture: the intended processor architecture for the app e.g. x86, AMD64, ARM64.
- isWindowsStoreApp: determines if the app is hosted inside an app container such as a Store app.
- statusBar: informs NVDA that an app places status bar somewhere other than bottom of the screen or requires other ways to obtain the status bar.
And other properties. Type dir(obj.appModule) from [Python Console](https://www.nvaccess.org/files/nvda/documentation/developerGuide.html#PythonConsole) for the complete list.

## The add-on development guide: Introduction to global plugins

### Example 1: Writing computer braille using QWERTY keyboard

You are meeting with a client who uses Duxbury braille translator (a popular braille document production program). This client is working with another user of NVDA who wishes to write computer braille from his computer keyboard everywhere. Based on this, you decide to write a global plugin and have found a module that allows the computer keyboard to act like a braille keyboard using a function.

The global plugin, named brailleWrite.py, would look like this:

    # An example global plugin.

    import qtbrl # The braille entry module.
    import globalPluginHandler
    from scriptHandler import script

    class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    	brlentry = False # Braille entry is not active.

    	@script(
    		description="Toggles braille entry on or off.",
    		gesture="kb:NVDA+X"
    	)
    	def script_toggleBrailleEntry(self, gesture):
    		self.brlentry = True if not self.brlentry else False # Toggle braille entry mode.

Notice that this command will not announce anything in speech on demand mode. See frequently asked questions for an explanation. Also, the add-on that implements braille entry using computer keyboards actually exists (called PCKBBRL).

With this background in mind, try some of the short exercises below.

### Exercises

- Write a global plugin named nvdaVersion.py to say the current NVDA version when NVDA+Shift+V is pressed.
- A user wants to hear the time announced every minute. Using the clock on the system tray, write a global plugin to announce when the time changes (hint: you need to use an event and check the role of the clock object).

### A Few more things to remember about global plugins

- When you write scripts in your global plugin, the commands you assign to them will take precedence (they are looked up first). Therefore, it is important to consult the NVDA user guide and documentation for other add-ons to minimize command conflicts.
- Each global plugin must be placed in globalPlugins directory in your add-on folder structure.
- It is possible to use more than one Python file in your global plugin. If this is the case, you need to put them in a folder (name must be the name of the plugin) inside globalPlugins folder, with the main plugin file named init.py.
- If you need to do something when the global plugin is loaded (such as loading the user configuration), you need to write an init method in your plugin class. In this method, you need to call the init method in the super (globalPluginHandler.GlobalPlugin) first before doing other startup work. Also, if you need to do something when the global plugin ends, define terminate method.
Let's go through some examples and exercises.

### The global plugin code

As shown earlier, the procedure for writing global plugins is same as writing any Python program, except that you import globalPluginHandler and put your add-on code in a class called `GlobalPlugin` which inherits from `globalPluginHandler.GlobalPlugin` (see the example in the first intro chapter). If you need to use third-party modules, you need to place the package in the same folder as the global plugin file and import the external module(s). Then define objects (usually overlay objects), methods and so on in your code.

### Introduction to global plugins

A global plugin adds features available everywhere. For example, if there is a control that will be used in many applications, then you can write a global plugin to handle them throughout NVDA. Another example is adding additional features to NVDA that can be used in all programs, such as OCR capability, place marker management and so on.

A global plugin is a Python source code (.py) file with the name of your plugin. For example, if you're adding support for rich edit fields in many applications, you can name your plugin as richEditSupport.py. When naming them, try to be brief so you can see what your plugin does.

IMPORTANT: although enhancers may appear to be identical with global plugins (and several enhancers were created as global plugins in the past), they are not the same. See Enhancers section for details.

### Typical development plan for global plugins

Typically, a global plugin is developed thus:

- You or someone suggests a feature or support for a particular control across different programs.
- You plan your global plugin (see the section on when to write or not write global plugins).
- You write your global plugin and test it. Once it is done and tested, you release the plugin.
Since global plugins are Python files, you can use the full power of python in your add-on code. Also, since global plugins have access to full power of NVDA code such as events, scripts and objects, you can use the concepts you learned from previous sections.

### When to write or not write global plugins

Since global plugins are used everywhere, you might be tempted to write support for a single application using global plugin alone. However, this is not the case. There are other guidelines to keep in mind when deciding whether to write a global plugin or not:

You might consider writing a global plugin if:

- You or a user wishes to use a certain feature everywhere.
- You need to support the same controls across different applications, provided that the control behaves the same in these programs.
- You need to register app module aliases. See the app modules chapter on how to do this.
- Define add-on specific command-line switches. This is covered in advanced code examples section.
You should not write a global plugin if:

- If you wish to enhance support for a single application.
- You are writing support for speech synthesizers or braille displays.
- You are defining custom braille tables and/or speech symbol dictionaries (these are not Python files and thus are not global plugins in a normal sense).

## The add-on development guide: Setting Up Your Add-on Development Environment

### Add-on Development Folder Structure

When writing add-ons, it is recommended that you store your add-on code in separate folders, one per add-on. If you choose to download the add-on template, the folder structure will be automatically created.

Once you install the needed dependencies (see above), see the section on how to package addons below.

### Add-on folder structure

Each add-on folder, at a minimum, must contain the following files and folders:

- manifest.ini to store manifest information such as add-on name, author, and compatibility range (minimum version, last tested version).
- An "addon" subfolder with the add-on module directory underneath this subfolder (appModules, globalPlugins, synthDrivers, brailleDisplayDrivers, visionEnhancementProviders, brailleTables). One or more module folders can be specified.
If you are using the add-on template, the folder structure will automatically be created, so you need to create only the addon subfolder and the add-on module folder(s) and code inside this folder. See the readme file in the template folder for more information on customizing your add-on manifest using the template files.

### Packaging add-ons

There are two ways of packaging add-ons:

- To package your add-on manually, zip up (compress) your add-on folder as a .zip file, then rename the file extension to .nvda-addon.
- To use the add-on template with SCons, open Command Prompt with administrator mode or Bash on Ubuntu on Windows (Windows 10 Anniversary Update with WSL enabled), change to your add-on folder and type `scons`.
For more information on add-on management, see the management chapter in this guide.

### System Requirements

To create an add-on for NVDA, please make sure your system meets the following requirements:

- NVDA:
    - A version of NVDA is available on your computer (either a portable or installed version will work, but we strongly recommend that you install a copy of NVDA on your development computer). Download NVDA from the [NV Access download page](https://www.nvaccess.org/download/).
    - Even better: we recommend installing the latest master (alpha) or beta development version to keep up to date with core API changes. You can download the latest snapshots at [nvaccess.org](https://www.nvaccess.org/files/nvda/snapshots/).
    - As of December 2025, NVDA alpha snapshots are 64-bit builds.
- Python:
    - Python 3.13 series, version 3.13.11 or later (64-bit for Windows): [python.org](https://www.python.org/downloads/release/python-31311/)
- SCons 4, version 4.10.1 or later for generating add-on packages: [scons.org](http://www.scons.org/)
- Markdown 3.8 or later for generating add-on documentation: [pypi.python.org](https://pypi.python.org/pypi/Markdown/3.7/)
- Optionally, you can pip install both scons and markdown from the command prompt, specifying the version if you wish.
- The GNU Gettext package for Windows for message localization support. You can choose one of the following options:
    - Manual Installation: Download the GNU Gettext package for Windows from [gnuwin32.sourceforge.net](http://gnuwin32.sourceforge.net/downlinks/gettext.php)
    - Once downloaded, install the application and add its executables to your environment variable. If you didn't change the directory during installation, the default location is: "C:\Program Files (x86)\GnuWin32\GetText\bin".
    - Automatic Installation: Download and install the Gettext for Windows installer from [mlocati.github.io](https://mlocati.github.io/articles/gettext-iconv-windows.html).
    - We recommend the static option during download, and not the shared. During the installation process, make sure to check the following options:
        - "&Add application directory to your environmental &PATH"
        - Set GETTEXTCLDRDIR environment variable (useful for msginit)
- If you are developing support for a program, speech synthesizer, or braille display, install the needed software and hardware.
- Optional Items:
    - Git 2.49.0 or later if you wish to upload the add-on to a repository such as [Bitbucket](https://bitbucket.org/) or [Github](https://www.github.com/) (optional. See below). You can use various Git clients, such as [Git Bash](https://www.atlassian.com/git/tutorials/git-bash), [Cygwin's Git](https://stackoverflow.com/questions/33006007/how-to-install-git-for-cygwin), and [TortoiseGit](https://tortoisegit.org/).
    - The [NVDA Community Add-on Template](https://github.com/nvaccess/AddonTemplate/archive/master.zip) (maintainer: NV Access) for ease of add-on file and folder packaging and management (optional).
Note: if you're using Windows 10 Anniversary Update or later and wish to use Ubuntu on Windows (AKA [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install-win10)), Python is already installed. You can then use Advanced Packaging Tool (APT) to obtain SCons and Gettext. You can then use pip to download and install Markdown.

## The add-on development guide: Sharing your add-on and experience with others

### The NV Access add-on store and code repository

To download or learn more about various add-ons created by NVDA users, visit NV Access add-on store accessible from NVDA menu/Tools. From the add-on store, you can browse, install, and update community add-ons, enable or disable add-ons, and view compatible or incompatible add-ons installed or published to the add-on store. See below on how to publish add-ons to the add-on store.

For developers wishing to read the code that powers various add-ons, you can search for add-on repositories stored on [GitHub](https://www.github.com/), which is also accessible when selecting "source code" from an add-on's context menu in the add-on store. The NVDA community add-on developers use [Git](https://www.git-scm.com) for version control.

Some of the useful and educational add-on repositories are:

- [Add-on Template](https://github.com/nvaccess/AddonTemplate/archive/master.zip): this is the source code repository for the community add-on template.
- [Place markers by Noelia Martinez](https://github.com/nvdaes/placeMarkers): adds place marker functionality and provides a good example of using text infos.
- [Windows App Essentials by Joseph Lee](https://github.com/josephsl/wintenApps): provides improved support for Windows 10 and later and various universal apps, considered a classic in how global plugins and app modules work together and includes examples of overlay classes and control behaviors that derives from UI Automation objects.
- [Read Feeds by Noelia Martinez](https://github.com/nvdaes/readFeeds): eases discovery of feeds on various websites and includes a simple example of storing and validating add-on settings.
- [NVDA Remote Support by Christopher Toth and Tyler Spivey](https://github.com/nvdaremote/nvdaremote): a popular add-on used for remote troubleshooting and technical support, provides examples of how various external Python libraries are used.
- [StationPlaylist by Joseph Lee](https://github.com/josephsl/stationPlaylist): improves usage of StationPlaylist Studio, provides interesting examples on overlay classes and app API, use of threads, and add-on dialogs and other user interfaces.

### The NVDA Add-ons list

If you want to keep in touch with your add-on users or want to learn from or contribute your add-on to others, please subscribe to [NVDA add-ons list][4]. This is a low traffic list devoted to discussing current and future add-ons, as well as to send and receive feedback on add-ons, including yours.

### Publishing add-ons for community distribution

If you would like to submit your add-on for distribution on NV Access add-on store, follow these steps:

- If you haven't, subscribe to NVDA Add-ons mailing list.
- Make sure your add-on meets the community submission checklist (see the next section).
- When you are ready, introduce the add-on. Be sure to specify name, author, brief description of the add-on, and public code repository if possible.
- Ask for community feedback. This is so that members (potential users and add-on authors) can use your add-on, report bugs, suggest features and changes, among other things.
- If you believe your add-on is ready for community distribution, inform the community and register the add-on on NV Access add-on store (GitHub username is required to fill out an online submission form). The add-on store registration steps are outlined below.
- Once your add-on is published on the add-on store, inform various communities, including users.
- For add-on updates, perform steps 4 through 6 and add a brief changelog that describes what the update contains. Make sure you go over the submission checklist again.
- Optionally, ask the community for more detailed feedback, including code audit, interface messages, additional compatibility checks, detailed security testing, and so on.

#### Add-on submission checklist

Your add-on:

- Must be licensed under GNU General Public license (GPL) version 2 which allows a GPL software such as NVDA to incorporate your code while it runs (add-ons are considered derivative works, according to NVDA license document).
    - The above statement applies to any part of the add-on that uses functionality provided by NVDA such as functions, classes, and modules.
    - Third-party modules can be included as long as you have appropriate license to do so (such as permission from vendors of proprietary software and/or using modules with licenses compatible with GPL 2 such as 3-Clause BSD license).
- Must be written in Python 3.
- Must be compatible with latest base API release (as of October 2025, base API is 2025.1.
- Messages to be presented to users should be made translatable (use _() Gettext function to make messages translatable). Be sure to accompany translatable messages with comments for translators (of the form: "`# Translators: description of message`", above the string containing the message).
- Add-ons to be registered on NV Access add-on store (see below for steps) must:
    - Use major.minor.patch or a similar scheme of the form number.number.number.
    - Minimum NVDA version must be 2019.1.
    - Last tested version must be the latest alpha version or earlier (as of December 2025, 2026.1 is the latest tested version value possible for add-ons under development/testing and 2025.3 for stable add-on releases).
    - Add-on URL must start with https.

#### NV Access add-on store submission process

- Upload the add-on (or an add-on update) to your add-on repository or a suitable location where the add-on package can be downloaded from (GitHub is recommended). Be sure to have the add-on download URL handy.
- Open [NV Access add-on store submission form](https://github.com/nvaccess/addon-datastore/issues/new?assignees=nvaccess&labels=autoSubmissionFromIssue&projects=&template=registerAddon.yml&title=%5BSubmit+add-on%5D%3A+) (you must be logged into GitHub to fill out this form).
- Fill out the form (submission name (typically add-on name and version), add-on package URL, source URL, publisher (GitHub username or your name and email address if needed), add-on channel (stable/beta/dev), license type (typically GPL v2), license URL).
- Select submit button.
- Submission results will be sent via email. If successful, a GitHub Actions notification will be shown with the submission issue closed. If not, failure reason will be displayed. For first-time add-on submitters (for new add-ons), approval from NV Access is required.

### Sharing your add-on and experience with others

Once you've finished developing your add-ons, you might want to share your code with others. Along the way, you might contribute your know-how so others may benefit from your experiences.

This chapter is designed to give some guidance on add-on release and maintenance, as well as connecting with your add-on users and other NVDA core and add-on developers around the world.

## The add-on development guide: Useful modules from NVDA core

### List of useful NVDA core modules and methods

The following lists useful NVDA core modules and some methods and classes found in those modules:

- Add-on Handler (addonHandler): The module which implements the add-on subsystem:
    - `addonHandler.initTranslation()`: Initializes internationalization support for your add-on.
    - `addonHandler.getCodeAddon()`: Retrieves the running instance of the add-on at the location of the function call, useful if wishing to locate add-on data such as name or version.
    - `addonHandler.isCLIParamKnown`: An accumulating decider to let the add-on define and handle custom command-line switches (discussed below).
- NVDA basic API (api.py): A collection of core methods used throughout NVDA, such as obtaining focus and navigator object, setting focus and so on. Some of the most useful functions are:
    - `api.getFocusObject()`: Retrieves the focused control (returns the object with focus).
    - `api.getNavigatorObject()`: Fetches the current navigator object. If NVDA is set to follow system focus, the focus and navigator object will be the same, otherwise a different object is returned.
    - `api.getForegroundObject()`: Returns the foreground window of the current application (the parent of this object is the application itself).
    - These have a corresponding method to set a certain object as the focus or navigator object. Note that this lets NVDA see the new focus or navigator object but does not actually change system focus.
    - `api.getDesktopObject()`: returns the shell (topmost level) object.
    - `api.copyToClip(text to be copied, optionally notify success or failure)`: copies text to the clipboard and optionally let NVDA notify the user about this operation.
- App Module subsystem (appModuleHandler.py, appModules): The subsystem in charge of handling app modules (see the chapter on app modules for more information). A useful function for the app module add-ons is:
    - `appModuleHandler.registerExecutableWithAppModule(alias executable name, base app module name)`: Informs NVDA to load the base app module if an alias app is running (discussed in detail in the ap modules chapter).
- ARIA support (aria.py): Implements support for Accessible Rich Internet Applications (ARIA).
- Base object collection (baseObject.py): Contains useful base objects such as scriptable objects (see the chapter on NVDA objects and overlay objects for more information).
- Braille input and output subsystem (braille.py, brailleInput.py): Controls braille output to and input from braille displays, needed by braille display driver add-ons.
- Braille display detector (bdDetect.py): Enables braille display device detection, needed by braille display drivers as part of their global plugin module if the display supports automatic hardware detection.
- Browse mode management (browseMode.py): Offers support for browse mode features such as single-letter navigation command definitions.
- Built-in modules (builtin.py): Allows access to builtin modules when working with add-ons.
- Configuration (config): Manages configuration and profiles.
- Content recognition engines (contentRecog packages): adds ability to use OCR and other methods to recognize content in various scenarios. NVDA offers built-in support for Windows OCR engine (Windows 10 and 11).
- Controls and states collection (controlTypes): Includes enumerations and dictionaries on control types (roles) and possible states that a control can be in.
- Core routines (core.py): Provides essential routines and features such as the main GUI loop.
- Display model support (displayModel.py): Provides features to work with text written directly to the screen.
- Events (eventHandler.py): Handles various events such as gaining focus. One function in particular is useful in app modules:
    - `eventHandler.requestEvents(event to be requested, process ID, window class name for the control)`: Allows NVDA to listen to specific events for certain controls while using another app.
    - `eventHandler.isPendingEvents(event name, object)`: Reports if events passed in for the specified object are pending.
- Extension points (extensionPoints): Provides a way to let add-ons and other modules define and respond to specific action such as profile switches, actions in an add-on and so on. The following extension points are defined:
    - `extensionPoints.Action`: Notifies when something happens e.g. profile switches.
    - `extensionPoints.Decider`: Decides whether to process something further e.g. processing keyboard input from a remote system.
    - `extensionPoints.AccumulatingDecider`: Similar to decider except all deciders will contribute to a decision to process something such as handling add-on specific command-line switches.
    - `extensionPoints.Filter`: Modifies a given text for further processing e.g. advanced speech sequences.
- Global Commands collection (globalCommands.py): A list of global commands available while using NVDA (see section on script scope for more information).
- Global Plugin subsystem (globalPluginHandler.py): The module needed for controlling global plugins.
- NVDA GUI (gui): A collection of classes used by NVDA to display its messages graphically. Includes GUI's for NVDA menu, settings panels and others.
- Hardware port utilities and input/output management (hwPortUtils.py, hwIo): A set of utilities for communicating over serial and other hardware ports, useful during driver add-on development.
- IAccessible support (IAccessibleHandler, IAccessible objects): Used for supporting Microsoft Active Accessibility (MSAA)/IAccessible controls.
- Input management (inputCore.py): Manages input from the user.
- Java support (JABHandler.py, JAB objects): A collection of methods used for supporting JAB (Java Access Bridge) subsystem used for Java applications.
- Keyboard input (keyboardHandler.py): Supports entering commands from the keyboard.
- Logging facility (logHandler.py): Allows a module to write logs to be viewed by a developer or a user via Log Viewer. It includes the following class:
    - `logHandler.Log`: The class which implements logging facility.
- Math content presentation (MathPress packages): Allows NVDA to recognize and interact with various math content and markup. NVDA ships with MathML support package (historical: and support for Math Player is included in 2015.2 or later).
- Mouse support (mouseHandler.py): Supports mouse commands.
- NVDA objects collection (NVDAObjects): A collection of NVDA objects or controls used in many applications and standards such as UIA (User Interface Automation). Some objects require special actions to be performed, and these are specified in behaviors module in NVDA objects package. Some of the common ones include:
    - `NVDAObjects.NVDAObject`: the base class for NVDA objects that define events, properties and so on.
    - `NVDAObjects.behaviors`: a collection of behaviors for specific controls, such as edit fields with or without selection detection, terminals, tool tips, help balloons, a way to simulate table commands in various controls and others.
    - `NVDAObjects.IAccessible`: a collection of MSAA/IAccessible objects, such as working with SysListView32 list views and others.
    - `NVDAObjects.JAB`: a collection of classes used when interfacing with Java applications and Java Access Bridge.
    - `NVDAObjects.UIA`: various classes for objects powered by UI Automation. It is also the home of a collection of controls used in legacy (not Chromium) Microsoft Edge and objects powered by EdgeHTML rendering engine.
    - `NVDAObjects.Window`: generic windows and other custom objects such as those found in Microsoft Excel.
- Audio device and output management (nvwave.py): Provides support for playing wave sounds:
    - `nvwave.getOutputDeviceNames(): Lists available audio devices connected and active on the system.
    - `nvwave.playWaveFile(file name)`: Plays the specified wave file (file path must exist).
- Review facility (review.py): assists with working with review cursor.
- Scripts support (scriptHandler.py): Handles scripts, methods executed due to the user pressing keyboard commands and other input.
    - scriptHandler.script: a decorator that allows information about the bound script to be defined while defining the script itself, including description (input help message), gesture/gestures (commands, the latter used for a list of gestures), and script category.
- Speech output (speech): Controls speech output.
- Synthesizer driver support (synthDriverHandler.py): This is the core module needed for speech synthesizer add-ons.
- Widget text access (textInfos): Allows access to text for widget and documents.
- Touchscreen support (touchHandler.py): Provides support for touchscreen input (installed versions only).
    - `touchHandler.touchSupported()`: returns if the system supports touch interaction.
- Tone output (tones.py): Allows the user to hear tones. The following function is defined:
    - `tones.beep(pitch in hertz, duration in milliseconds, left channel volume, right channel volume)`: Plays a tone of specified pitch for specified duration. The first two arguments are mandatory, while the other two are optional.
- User interface messages (ui.py): Includes various functions for speech and/or braille output, including:
    - `ui.message(message to be spoken/brailled, speech priority, optional braille message)`: Speaks or brailles the message (a string surrounded by quotes). Optionally, speech priority can be specified to interrupt what the speech synthesizer is saying when announcing the message, as well as output a different message on braille displays.
    - `ui.browseableMessage(message to be shown, title, HTML or not, sanitize content, add copy button, add close button)`: displays some text and an optional title in a web browser window. If you want to use HTML markup, set isHTML argument to True. The sanitize content option prevents security issues while processing HTML content. A copy to clipboard button and/or a close button can be added.
- UIA support (UIAHandler.py, UIA objects): Used for supporting UIA (User Interface Automation) controls.
- Useful utility features (utils): Offers utilities such as display enumeration strings and scheduling tasks.
- Virtual buffers (virtualBuffers): Handles virtual buffer documents such as web sites.
- Windows version specifications and checks (winVersion.py): provides constants representing Windows releases and comparing Windows releases.
    - winVersion.getWinVer(): returns the current Windows release (Windows release name, major.minor.build, installation type, and service pack if any). This data can be compared with other Windows releases such as detecting specific Windows 10 release such as October 2018 Update e.g. winVersion.getWinVer() >= winVersion.WIN10_1809.
- Windows API wrappers: the following modules are thin wrappers around Windows API libraries. You can use these modules or call Windows API directly via ctypes.windll.dllname (e.g. ctypes.windll.user32):
    - `winKernel`: Wraps some constants, structures and functions from kernel32.dll that are commonly encountered in NVDA.
    - `winUser`: wraps around constants, structures and functions defined in user32.dll that are used by NVDA.
The modules without .py extension are directories, containing specialist modules. There are other useful methods out there in addition to the list above, but the above are the most useful ones. See the NVDA source code documentation for other methods, or see the examples below on how these methods and others are used throughout the life of an add-on.

### Some real-life examples

Let's go through some simplified real-life examples demonstrating how the components listed above are used in common add-on writing scenarios.

#### Example 1: am I on the right app where the focus is located?

The following code checks whether the navigator object is located somewhere on the same app or not.

    import api

    def sameApp(obj=None):
    	if obj is None:
    		obj = api.getNavigatorObject()
    	return api.getFocusObject().appModule == obj.appModule

The `api.getNavigatorObject()` function returns the current navigator object, the object you are interested in as opposed to focused object. Each NVDA object includes `appModule` member which records on which app an object is located.

#### Example 2: Display a message in a browse mode document

It is possible to display a message in a browse mode window so people can use browse mode commands to review the message content. The below code displays "Hello world" in a document window.

    import ui

    ui.browseableMessage("Hello World!", isHtml=False)

The isHtml flag tells NVDA whether to treat the message as HTML text.

#### Example 3: Announce the automation ID of a UIA object

In UI Automation, automation ID is used to identify different screen elements. The following code displays this information in a browsable window.

    import ui
    from NVDAObjects.UIA import UIA

    def announceUIAId():
    	obj = api.getFocusObject()
    	if isinstance(obj, UIA):
    		ui.browseableMessage(obj.UIAAutomationId, isHtml=True)

#### Example 4: Send keystrokes

You can ask NVDA to send specific keystrokes by instantiating a keyboard gesture object.

    import keyboardHandler

    def sendApplicationsKey():
    	keyboardHandler.KeyboardInputGesture.fromName("applications").send()

#### Example 5: Stop speech whenever screen content changes if dynamic content change announcement is off

The following code is a handler for a name change event that stops speech whenever screen content changes if dynamic content change announcement is off.

    import appModuleHandler
    import config
    import speech

    class AppModule(appModuleHandler.AppModule):

    	def event_nameChange(self, obj, nextHandler):
    		if not config.conf["presentation"]["reportDynamicContentChanges"]:
    			speech.cancelSpeech()

#### Example 6: using script decorator

A decorator is a function that wraps and returns another function while performing internal operations. For example, a decorator can make changes to the internals of a function or check something on behalf of another function without the wrapped function being aware of what's happening.

NVDA includes a decorator named scriptHandler.script to make it easier to define information about a script. A script's description (input help mode message), gesture or gestures (commands bound to this script), script category, and participation in speech on demand mode (let NVDA anounce things while keeping other scripts silent, see below example) can be assigned as you define the script.

Recall the first example where a beep was heard when NVDA+A was pressed. The drawback is that the actual script and the command (gesture) associated with it were defined in different places. You can group them by using script decorator (scriptHandler.script) as shown below.

    # Add-on development first example global plugin, now edited to use script decorator

    import globalPluginHandler
    import scriptHandler
    import tones

    class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    	@scriptHandler.script(gesture="kb:NVDA+A")
    	def script_doBeep(self, gesture):
    		tones.beep(440, 1000)  # Beep a standard middle A for 1 second.

#### Example 7: speech on demand script

Sometimes it is helpful to let NVDA stay silent while working on something and offer commands to report status such as screen content. If you are defining scripts to announce screen content and other informational commands, you can let your script participate in speech on demand mode, a mode to let NVDA announce various information while silencing other commands.

In the below example, NVDA will say "I am NVDA" when Control+NVDA+1 (number row 1) is pressed. A follow-up example will tweak it slightly.

    # Add-on development example global plugin without speech on demand flag

    import globalPluginHandler
    import scriptHandler
    import ui

    class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    	@scriptHandler.script(gesture="kb:control+NVDA+1")
    	def script_sayGreeting(self, gesture):
    		ui.message("I am NVDA")

Compare this with the example below where "speakOnDemand" flag is added:

    # Add-on development example global plugin with speech on demand flag

    import globalPluginHandler
    import scriptHandler
    import ui

    class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    	@scriptHandler.script(gesture="kb:control+NVDA+1", speakOnDemand=True)
    	def script_sayGreeting(self, gesture):
    		ui.message("I am NVDA")

In summary, without speak on demand flag (default is False), NVDA will not say "I am NVDA" when Control+NVDA+1 is pressed while in speech on demand mode. But with the "speakOnDemand" flag, NVDA will say "I am NVDA" even in speech on demand mode. There are caveats with speech on demand mode and are documented as a frequently asked question later in this guide.

Throughout this guide, whenever script examples are shown, script decorator without speak on demand mode will be used unless noted otherwise.

This is just a sample of things you can encounter as you write add-ons and how you can use various NVDA components to achieve what you want. We'll tour add-on components and meet more functions throughout this guide.

### Useful modules from NVDA core

Throughout the life of add-on development, you'll come across some useful modules from NVDA core that would be helpful in your add-on code. This section explains them and some functions in those modules that would be useful, along with examples that utilize some of them.

Note: for readers who are scripters for other screen readers, see Appendix D on equivalent functions between screen reader scripting facilities.

## The NVDA developer guide: Extension Points

### addonHandler

Type

Extension Point

Description

`AccumulatingDecider`

`isCLIParamKnown`

Allows adding NVDA commandline parameters which apply to plugins. See this section of the Dev Guide for more information.

### braille

Type

Extension Point

Description

`Filter`

`filter_displaySize`

[Deprecated] Allows components or add-ons to change the display size used for braille output.

`Filter`

`filter_displayDimensions`

Allows components or add-ons to change the number of rows and columns of the display used for braille output.

`Action`

`displaySizeChanged`

Notifies of display size changes.

`Action`

`pre_writeCells`

Notifies when cells are about to be written to a braille display

`Action`

`displayChanged`

Notifies of braille display changes.

`Decider`

`decide_enabled`

Allows deciding whether the braille handler should be forcefully disabled.

### config

Type

Extension Point

Description

`Action`

`post_configProfileSwitch`

Notifies after the configuration profile has been switched.

`Action`

`pre_configSave`

Notifies before NVDA's configuration is saved to disk.

`Action`

`post_configSave`

Notifies after NVDA's configuration has been saved to disk.

`Action`

`pre_configReset`

Notifies before configuration is reloaded from disk or factory defaults are applied.

`Action`

`post_configReset`

Notifies after configuration has been reloaded from disk or factory defaults were applied.

### Extension Points

NVDA's `extensionPoints` module allows code in different parts of NVDA, or in add-ons, to perform tasks such as:

- Be notified when an action occurs or a state is changed.
- Receive, as part of being notified, variables related to the action or changed state.
- Cancel or alter an action NVDA was going to take, based upon certain conditions.
- Modify data that NVDA is using (such as changing speech sequences or braille, before they are spoken or brailled).
- Delay something NVDA is doing, while intervening operations are performed.
There are five kinds of extension point:

Type

Purpose

`Action`

Allows some code to find out what other code is doing. For example, an add-on can be notified before or after a config profile changes.

`Filter`

Edits data. A filter registered in the speech module, might allow changing speech strings before they are spoken.

`Decider`

Runs each registered handler until one of them returns `False`. If one does, it can be used to prevent the invoking code from running.

`AccumulatingDecider`

Like `Decider`, but always runs all of its registered handlers, and only decides if one of them failed at the end. The expected result of each is `True` by default, though expecting `False` is possible.

`Chain`

Allows registering handlers that return iterables (mainly generators). Calling `iter` on the `Chain` returns a generator that iterates over all the handlers.

The sections below provide the list of currently defined extension points in NVDA, along with brief descriptions for them. Please see code documentation in the associated files, or the code itself, for further explanation. The section titles below represent the package or module in which the listed extension points are defined.

For examples of how to define and use new extension points, please see the code documentation of the `extensionPoints` package.

### inputCore

Type

Extension Point

Description

`Decider`

`decide_handleRawKey`

Notifies when a raw keyboard event is received, before any NVDA processing, allowing other code to decide if it should be handled.

`Decider`

`decide_executeGesture`

Notifies when a gesture is about to be executed, allowing other code to decide if it should be.

### logHandler

Type

Extension Point

Description

`Action`

`_onErrorSoundRequested`

Triggered every time an error sound needs to be played. This extension point should not be used directly but retrieved calling `getOnErrorSoundRequested()` instead.

### nvwave

Type

Extension Point

Description

`Decider`

`decide_playWaveFile`

Notifies when a wave file is about to be played, allowing other code to decide if it should be.

### speech

Type

Extension Point

Description

`Action`

`speechCanceled`

Triggered when speech is canceled.

`Action`

`pre_speechCanceled`

Triggered before speech is canceled.

`Action`

`pre_speech`

Triggered before NVDA handles prepared speech.

`Action`

`post_speechPaused`

Triggered when speech is paused or resumed.

`Action`

`pre_speechQueued`

Triggered after speech is processed and normalized and directly before it is enqueued.

`Filter`

`filter_speechSequence`

Allows components or add-ons to filter speech sequence before it passes to the synth driver.

### synthDriverHandler

Type

Extension Point

Description

`Action`

`synthIndexReached`

Notifies when a synthesizer reaches an index during speech.

`Action`

`synthDoneSpeaking`

Notifies when a synthesizer finishes speaking.

`Action`

`synthChanged`

Notifies of synthesizer changes.

`Action`

`pre_synthSpeak`

Notifies when the current synthesizer is about to speak something.

### tones

Type

Extension Point

Description

`Decider`

`decide_beep`

Notifies when a beep is about to be generated and played, allowing a component to decide whether it should be.

### vision.visionHandlerExtensionPoints.EventExtensionPoints

These extension points are expected to be used and registered to differently than other extension points. Please see the `EventExtensionPoints` class documentation for more information, and detailed descriptions.

Type

Extension Point

Notifies a vision enhancement provider when ...

`Action`

`post_objectUpdate`

an object property has changed.

`Action`

`post_focusChange`

the focused NVDAObject has changed.

`Action`

`post_foregroundChange`

the foreground NVDAObject has changed.

`Action`

`post_caretMove`

a physical caret has moved.

`Action`

`post_browseModeMove`

a virtual caret has moved.

`Action`

`post_reviewMove`

the position of the review cursor has changed.

`Action`

`post_mouseMove`

the mouse has moved.

`Action`

`post_coreCycle`

the end of each core cycle has been reached.

## The NVDA developer guide: Introduction

### Add-on API stability

#### Definition of the public API

The NVDA Add-on API consists of all NVDA Python objects, classes and functions, excluding symbols prefixed with an underscore (`_`), transitive imports and Python packages.

- Public symbols (e.g. `gui.mainFrame`): These form the supported contract. We strive to maintain backward compatibility for these symbols according to the schedule below.
- Private symbols (e.g. `_doInstall`): These are internal implementation details. Code is considered private if it begins with a leading underscore. This also includes anything "below" the underscore. For example, `package.module._Class`, `package._module.Class`, and `_package.module.Class` are all internal. They may change or disappear in any release without notice. Add-ons relying on private symbols do so at their own risk.
- Pip packages: These may be updated, downgraded or removed at any time. It is recommended to package any pip dependency directly with your add-on, rather than using NVDA's version of the package. The exception to this is `wxPython`, where any breaking changes from `wxPython` will be treated as an API breaking change.

#### The API release cycle

To balance progress with ecosystem stability, NVDA follows a predictable schedule for API changes:

- Annual API-breaking release (major releases, e.g. 2026.1): This is the only release window where signature breaking changes (defined below) are permitted. This allows us to remove technical debt and refactor core code.
- Standard releases (minor & patch releases, e.g. 2026.2, 2026.3.1): These releases focus on features and stability. Existing API signatures are preserved, but new API features may be added. This includes behavioural refinements and bug fixes (see below).

#### Classification of API changes

To provide clarity on what add-on developers can expect, we categorise changes into three tiers:

##### Signature breaking changes

- Examples: Renaming a function, removing a module, changing a function’s return type or removing/reordering positional arguments.
- Policy: These occur only in the .1 release (e.g. 2026.1).

##### Behavioural refinements & bug fixes

A change where the code continues to run (the signature matches), but the logic or outcome changes to correct a defect or security flaw.

- Examples: Fixing a math error or optimising an algorithm (e.g. changing a sort order).
- Policy: These are permitted in any major or minor release (e.g. 2026.1, 2026.2).
- We recognise that some add-ons may rely on incorrect behaviour or bugs. However, preserving a bug to maintain backwards compatibility significantly hampers NVDA's development. If a public function was documented to do X but was actually doing Y, changing it to correctly do X is considered a bug fix, not a breaking change.

##### Security improvements

Security takes precedence over backward compatibility. We will make every effort to document these changes clearly (see below).

- Examples: Privilege escalation or insecure file handling.
- Policy: These are permitted in any release but are primarily deployed in patch releases (e.g. 2026.1.2).
- In the rare event that a security fix requires a signature breaking change outside of the annual API-breaking release:
- If the change is likely to cause instability in existing add-ons, we will treat the patch as an official API-breaking release (forcing a global add-on compatibility update) to ensure user safety.
- If our analysis indicates the affected API is not widely used, we reserve the right to deploy the fix without forcing a global compatibility update.

#### API deprecation strategy

We aim to avoid silent breaks of add-on code. When removing or changing APIs in a breaking release (e.g. 2026.1) or due to an urgent security improvement (e.g. 2026.1.2):

- We will mark functions as deprecated, where possible, in the releases leading up to the break (e.g. raising a `DeprecationWarning` in 2025.4).
- All API breaking changes will be listed in the "Changes for Developers" section of the What's New document, and the [NVDA Add-on API Announcements](https://groups.google.com/a/nvaccess.org/g/nvda-api) email group.

#### Stability of transitive imports in the API

Make sure to import your code from the original module by checking the NVDA source code.

e.g. if a class is located at `foo.py`, you should import it as follows:

    from foo import Foo

If `bar.py` imports `Foo` you cannot rely on importing `Foo` from `bar`. i.e. you must import it directly from `foo`.

The following is not supported in the API, as the import in `bar` could be removed at any time.

    from bar import Foo

#### Stability of pip packages

Pip packages may be updated, downgraded, or removed at any time. It is recommended to package any pip dependency you share with NVDA directly with your add-on, rather than using NVDA's version of the package.

### C++

Some of NVDA is written in C++, e.g. nvdaHelper. For an overview of nvdaHelper, including how to configure Visual Studio to enable intellisense see the [nvdaHelper readme](https://github.com/nvaccess/nvda/blob/master/nvdaHelper/readme.md)

### A Note About Python

NVDA and its components are primarily written in the Python programming language. It is not the goal of this guide to teach you Python, though examples are provided through out this guide which will help to familiarise you with the Python syntax. Documentation and other resources related to the Python language can be found at www.python.org/

## The NVDA developer guide: NVDA Python Console

### Namespace

#### Automatic Imports

For convenience, the following modules and variables are automatically imported in the console: sys, os, wx, log (from logHandler), api, queueHandler, config, controlTypes, textInfos, braille, speech, vision, appModules, globalPlugins

See: pythonConsole.PythonConsole.initNamespace

#### Snapshot Variables

Whenever NVDA+control+z is pressed, certain variables available in the console will be assigned according to the current state of NVDA. These variables are:

- `focus`: The current focus object
- `focusAnc`: The ancestors of the current focus object
- `fdl`: Focus difference level; i.e. the level at which the ancestors for the current and previous focus differ
- `fg`: The current foreground object
- `nav`: The current navigator object
- `caretObj`: The object which contains the caret (focus or tree interceptor if any)
- `caretPos`: A text info at the position of the caret
- `review`: The current `TextInfo` instance representing the user's review position
- `mouse`: The current mouse object
- `brlRegions`: The braille regions from the active braille buffer

### Tab completion

The input control supports tab-completion of variables and member attribute names. Hit the tab key once to complete the current input if there is one single candidate. If there is more than one, hit the tab key a second time to open a menu listing all matching possibilities. By default, only "public" member attributes are listed. That is, if the input is "nav.", attribute names with no leading underscore are proposed. If the input is "nav._", attribute names with a single leading underscore are proposed. Similarly, if the input is "nav.__", attribute names with two leading underscores are proposed.

### Usage (The NVDA developer guide: NVDA Python Console)

The console can be activated in two ways:

- By pressing NVDA+control+z. If activated in this fashion, a snapshot of the current state of NVDA at the time the key was pressed will be taken and saved in certain variables available in the console. See Snapshot Variables for more details.
- By selecting Tools -> Python console from the NVDA system tray menu.
The console is similar to the standard interactive Python interpreter. Input is accepted one line at a time and processed when enter is pressed. Multiple lines can be pasted at once from the clipboard and will be processed one by one. You can navigate through the history of previously entered lines using the up and down arrow keys.

Output (responses from the interpreter) will be spoken when enter is pressed. The f6 key toggles between the input and output controls. When on the output control, alt+up/down jumps to the previous/next result (add shift for selecting). Pressing control+l clears the output.

The result of the last executed command is stored in the "_" global variable. This shadows the gettext function which is stored as a built-in with the same name. It can be unshadowed by executing `del _` and avoided altogether by executing `_ = _`.

Closing the console window (with escape or alt+F4) simply hides it. This allows the user to return to the session as it was left when it was closed, including history and variables.

## The NVDA developer guide: Packaging Code as NVDA Add-ons

### Add-on Documentation

Documentation for an add-on should be placed in the `doc` directory in the archive. Similar to the `locale` directory, this directory should contain directories for each language in which documentation is available.

Users can access documentation for a particular add-on by opening the Add-on Store, selecting the add-on and pressing the Add-on help button. This will open the file named in the docFileName parameter of the manifest. NVDA will search for this file in the appropriate language directories. For example, if docFileName is set to readme.html and the user is using English, NVDA will open doc\en\readme.html.

### Braille translation tables

Although NVDA ships with more than a hundred braille translation tables provided by [the liblouis project](https://liblouis.io/) aimed at fitting most needs, it also supports the addition of custom tables. Custom tables must be placed in the brailleTables directory of an add-on or subdirectory of the scratchpad directory. These tables can either replace standard tables shipped with NVDA or be completely new ones.

When adding a table, some information must be provided such as its display name in the Preferences dialog, whether it supports input and/or output and whether it is for contracted braille. When an add-on ships with tables, this information is included in its manifest in the optional brailleTables section. For example:

    [brailleTables]
    [[fr-bfu-tabmod-comp8.utb]]
    displayName = French (unified) 8 dot computer braille - Addition
    contracted = False
    output = True
    input = True

    [[no-no-8dot.utb]]
    displayName = Norwegian 8 dot computer braille - Replacement
    contracted = False
    output = True
    input = True

In the above example, `fr-bfu-tabmod-comp8.utb` is a new table, while `no-no-8dot.utb` replaces a table that is already included in NVDA. Both tables need to be shipped in the brailleTables directory of the add-on. It is also possible to include a table in the manifest that is shipped with NVDA but otherwise unavailable for selection in the Preferences dialog. In that case, the table does not need to be shipped in the add-on's brailleTables directory.

Providing a custom table, whether it has the same file name as a standard table or a different name, thus requires you to define the table in the add-on's manifest. The only exception to this rule applies to tables that are included within other tables. While they don't have to be included in the manifest of the add-on, they can only be included from other tables that are part of the same add-on.

Note that for the display name of the table to be translated, an entry should be added to a locale manifest. For example, add the following to `locale\fr\manifest.ini`:

    [brailleTables]
    [[no-no-8dot.utb]]
    displayName = Norvégien Braille informatique 8 points - Remplacement

Custom tables can also be placed in the brailleTables subdirectory of the scratchpad directory. In this case, the table metadata can be placed in a `manifest.ini` file in the root of the scratchpad in the exact same format as the example above. Basically, this means that, whether using an add-on or the scratchpad, the requirements and implementation steps are equal. Note that a `manifest.ini` file in the scratchpad is only parsed for braille table metadata. Other add-on metadata in the file is ignored.

Please refer to the [liblouis documentation](https://liblouis.io/documentation/) for detailed information regarding the braille translation tables format.

### Localizing Add-ons

It is possible to provide locale-specific information and messages for your add-on. Locale information can be stored in a locale directory in the archive. This directory should contain directories for each language it supports, using the same language code format as the rest of NVDA; e.g. en for English, fr_CA for French Canadian.

#### Locale-specific Manifest Files

Each of these language directories can contain a locale-specific manifest file called manifest.ini, which can contain a small subset of the manifest fields for translation. These fields are `summary` and `description`. You can also override the `displayName` field for speech symbol dictionaries and braille translation tables. All other fields will be ignored.

#### Locale-specific Messages

Each language directory can also contain gettext information, which is the system used to translate the rest of NVDA's user interface and reported messages. As with the rest of NVDA, an `nvda.mo` compiled gettext database file should be placed in the `LC_MESSAGES` directory within this directory. To allow plugins in your add-on to access gettext message information via calls to `_()`, `ngettext()`, `npgettext()` and `pgettext()` you must initialize translations at the top of each Python module by calling `addonHandler.initTranslation()`. This function cannot be called in modules that do not belong to an add-on, e.g. in a scratchpad subdirectory. For more information about gettext and NVDA translation in general, please read the [Translating NVDA page](https://github.com/nvaccess/nvda/blob/master/projectDocs/translating/readme.md)

#### Symbol dictionaries

You can provide custom speech symbol dictionaries in add-ons to improve symbol pronunciation. The process to create custom speech symbol dictionaries is very similar to that of the translation process of existing symbols. Note that complex symbols are not supported.

Custom symbol dictionaries must be placed in a language directory and have a filename in the form `symbols-<name>.dic`, where `<name>` is the name that has to be provided in the add-ons manifest. All locales implicitly inherit the symbol information for English, though any of this information can be overridden for specific locales.

When adding a symbol dictionary not marked as mandatory, some information must be provided such as its display name, since it should be shown in the speech category of the settings dialog. A symbol dictionary can also be marked mandatory, in which case it is always enabled with the add-on. When an add-on ships with symbol dictionaries, this information is included in its manifest in the optional `symbolDictionaries` section. For example:

    [symbolDictionaries]
    	[[greek]]
    		displayName = Greek
    		mandatory = false

    	[[hebrew]]
    		displayName = Biblical Hebrew
    		mandatory = true

In the above example, `greek` is a symbol dictionary that is optional and will be listed in the speech category of NVDA's settings dialog under the "Extra dictionaries for character and symbol processing" setting. Its file will be stored as `locale\en\symbols-greek.dic`, whereas French translations of the symbols are stored in `locale\fr\symbols-greek.dic`. When using NVDA in French, symbols that aren't defined in the French dictionary inherit the symbol information for English.

Also in the example, the `hebrew` dictionary is marked mandatory and will therefore always be enabled as long as the add-on is active. Its file will be stored as `locale\en\symbols-hebrew.dic`, whereas French translations of the symbols are stored in `locale\fr\symbols-hebrew.dic`.

Note that for the display name of the symbol dictionary to be translated, an entry should be added to a locale manifest. For example, add the following to `locale\fr\manifest.ini`:

    [symbolDictionaries]
    	[[hebrew]]
    		displayName = Hébreu Biblique

### Manifest Files

Each add-on package must contain a manifest file named manifest.ini. This must be a UTF-8 encoded text file. This manifest file contains key = value pairs declaring info such as the add-on's name, version and description.

#### Available Fields

Although it is highly suggested that manifests contain all fields, the fields marked as mandatory must be included. Otherwise, the add-on will not install.

- name (string, required): A short, unique, name for the add-on.
    - The recommended convention is lowerCamelCase.
    - This is used to differentiate add-ons internally, and is also used as the name of the add-on's directory in the user configuration directory.
    - Special characters should be avoided as the add-on name will be used as a folder name. Expected characters are alphanumeric, space, underscore and hyphen.
- summary (string, required): The name of the add-on as shown to the user.
- version (string, required): The version of this add-on; e.g. 2.0.1. When uploading to the Add-on Store certain requirements apply:
    - Using `<major>.<minor>` or `<major>.<minor>.<patch>` format.
    - For a user to be able to update to this add-on, the version must be greater than the last version uploaded.
    - Add-on versions are expected to be unique for the addon name and channel, meaning that a beta, stable and dev version of the same add-on cannot share a version number. This is so there can be a unique ordering of newest to oldest.
    - The suggested convention is to increment the patch version number for dev versions, increment the minor version number for beta versions, and increment the major version number for stable versions.
- author (string, required): The author of this add-on, preferably in the form `Full Name <email address>`; e.g. `Michael Curran <[email protected]>`.
- description (string): A sentence or two describing what the add-on does.
- changelog (string): A list of changes between previous and latest add-on releases.
    - This is used to inform users about changes included in the add-on release.
    - Changes can include new features, changes, bug fixes, and localization updates if any.
    - Markdown can be used to format the list of changes, as they will be converted to HTML to be shown in browse mode.
    - When releasing add-on updates, changes should be edited if possible. This means not all add-on releases will include notable changes.
- url (string): A URL where this add-on, further info and upgrades can be found.
    - Starting the URL with `https://` is required for submitting to the Add-on Store.
- docFileName (string): The name of the main documentation file for this add-on; e.g. readme.html. See the Add-on Documentation section for more details.
- minimumNVDAVersion (string, required): The minimum required version of NVDA for this add-on to be installed or enabled.
    - e.g "2021.1"
    - Must be a three part version string i.e. Year.Major.Minor, or a two part version string of Year.Major. In the second case, Minor defaults to 0.
    - Defaults to "0.0.0"
    - Must be less than or equal to `lastTestedNVDAVersion`
    - This must match a valid API version to be submitted to the Add-on Store. Valid API versions are found [on GitHub](https://github.com/nvaccess/addon-datastore-transform/blob/main/nvdaAPIVersions.json).
- lastTestedNVDAVersion (string, required): The last version of NVDA this add-on has been tested with.
    - e.g "2022.3.3"
    - Must be a three part version string i.e. Year.Major.Minor, or a two part version string of Year.Major. In the second case, Minor defaults to 0.
    - Defaults to "0.0.0"
    - Must be greater than or equal to `minimumNVDAVersion`
    - This must match a valid API version to be submitted to the Add-on Store. Valid API versions are found [on GitHub](https://github.com/nvaccess/addon-datastore-transform/blob/main/nvdaAPIVersions.json).
All string values must be enclosed in quotes as shown in the example below.

The lastTestedNVDAVersion field in particular is used to ensure that users can be confident about installing an add-on. It allows the add-on author to make an assurance that the add-on will not cause instability, or break the users system. When this is not provided, or is less than the current version of NVDA (ignoring minor point updates e.g. 2018.3.1) then the user will be warned not to install the add-on.

The manifest can also specify information regarding any additional speech dictionaries, symbol or braille translation tables provided by the add-on. Please refer to the speech dictionaries, symbol dictionaries and braille translation tables sections.

#### An Example Manifest File

    name = "myTestAddon"
    summary = "Cool Test Add-on"
    version = "1.0.0"
    description = "An example add-on showing how to create add-ons!"
    author = "Michael Curran <[email protected]>"
    url = "[github.com](https://github.com/nvaccess/nvda/blob/master/projectDocs/dev/addons.md)"
    docFileName = "readme.html"
    minimumNVDAVersion = "2021.1"
    lastTestedNVDAVersion = "2022.3.3"

### Non-ASCII File Names in Zip Archives

If your add-on includes files which contain non-ASCII (non-English) characters, you should create the zip archive such that it uses UTF-8 file names. This means that these files can be extracted properly on all systems, regardless of the system's configured language. Unfortunately, many zip archivers do not support this, including Windows Explorer. Generally, it has to be explicitly enabled even in archivers that do support it. [7-Zip](http://www.7-zip.org/) supports this, though it must be enabled by specifying the "cu=on" method parameter.

### Optional install / Uninstall code

If you need to execute code as your add-on is being installed or uninstalled from NVDA (e.g. to validate license information or to copy files to a custom location), you can provide a Python file called `installTasks.py` in the archive which contains special functions that NVDA will call while installing or uninstalling your add-on. This file should avoid loading any modules that are not absolutely necessary, especially Python C extensions or dlls from your own add-on, as this could cause later removal of the add-on to fail. However, if this does happen, the add-on directory will be renamed and then deleted after the next restart of NVDA. Finally, it should not depend on the existence or state of other add-ons, as they may not be installed, may have already been removed or may not yet be initialized.

#### the onInstall function

NVDA will look for and execute an `onInstall` function in `installTasks.py` after it has finished extracting the add-on into NVDA. Note that although the add-on will have been extracted at this point, its directory will have a `.pendingInstall` suffix until NVDA is restarted, the directory is renamed and the add-on is really loaded for the first time. If this function raises an exception, the installation of the add-on will fail and its directory will be cleaned up.

#### The onUninstall Function

NVDA will look for and execute an `onUninstall` function in `installTasks.py` when NVDA is restarted after the user has chosen to remove the add-on. After this function completes, the add-on's directory will automatically be removed. As this happens on NVDA startup before other components are initialized, this function cannot request input from the user.

### Packaging Code as NVDA Add-ons

Add-ons make it easy for users to share and install plugins, drivers, speech pronunciation/symbol dictionaries and braille translation tables. They can be packaged in to a single NVDA add-on package, which the user can then install into a copy of NVDA via the Add-on Store found under Tools in the NVDA menu. An add-on package is simply a standard zip archive with the file extension of "`nvda-addon`". It can contain a manifest file, install/uninstall code and directories containing plugins, drivers, speech dictionaries, symbol dictionaries and braille translation tables.

### Plugins and Drivers

The following plugins and drivers can be included in an add-on:

- App modules: Place them in an `appModules` directory in the archive.
- Braille display drivers: Place them in a `brailleDisplayDrivers` directory in the archive.
- Global plugins: Place them in a `globalPlugins` directory in the archive.
- Synthesizer drivers: Place them in a `synthDrivers` directory in the archive.
- Speech dictionaries: Place them in the `speechDicts` directory with a file name with the `.dic` extension, e.g. `speechDicts\pronunciation.dic`.
- Symbol dictionaries: Place them in the directory for one or more locales with a file name of `symbols-<name>.dic`, e.g. `locale\en\symbols-greek.dic`.
- Braille translation tables: Place them in a `brailleTables` directory in the archive.

### Speech dictionaries

You can provide custom speech dictionaries in add-ons to improve pronunciation of words that are usually pronounced incorrectly by speech synthesizers. Custom dictionaries must be placed in the `speechDicts` directory and have a filename with the `.dic` extension. For example, when your dictionary is named `<name>.dic`, `<name>` is the name that has to be provided in the add-ons manifest.

When adding a speech dictionary not marked as mandatory, some information must be provided such as its display name, since it should be shown in the speech category of the settings dialog. A speech dictionary can also be marked mandatory, in which case it is always enabled with the add-on. When an add-on ships with speech dictionaries, this information is included in its manifest in the optional `speechDictionaries` section. For example:

    [speechDictionaries]
    	[[pronunciation]]
    		displayName = Dodgy Dictionary
    		mandatory = false

In the above example, `pronunciation` is a dictionary that is optional and will be listed in the speech category of NVDA's settings dialog under the "Speech Dictionaries" setting. Its file will be stored as `speechDicts\pronunciation.dic`. When you mark the dictionary as mandatory, it will be always enabled as long as the add-on is active.

Note that for the display name of the dictionary to be translated, an entry should be added to a locale manifest. For example, add the following to `locale\fr\manifest.ini`:

    [speechDictionaries]
    	[[pronunciation]]
    		displayName = Dictionnaire douteux

Unlike symbol dictionaries, speech dictionaries are currently locale-agnostic. Therefore, an active dictionary is always active, regardless of the current language.

#### Creating speech dictionaries

A speech dictionary file contains dictionary rules, one per line. Each dictionary rule consists of four tab-separated fields on a single line:

    <pattern>	<replacement>	<caseSensitive>	<type>

The fields are:

- `pattern`: The text pattern to match. Hash characters (`#`) must be escaped as `\#`.
- `replacement`: The text to replace the matched pattern with. Hash characters (`#`) must be escaped as `\#`.
- `caseSensitive`: A numeric flag indicating case sensitivity: * `0`: Case insensitive matching * `1`: Case sensitive matching
- `type`: A number indicating the type of pattern matching to use: * `0`: Anywhere - Pattern can match anywhere in the text (literal string) * `1`: Regular expression - Pattern is treated as a Python regular expression * `2`: Whole word - Pattern must match a complete word with word boundaries on both sides * `3`: Part of word - Pattern must be preceded or followed by a word character (letter, digit, underscore) * `4`: Start of word - Pattern must have a word boundary at the start and a word character at the end * `5`: End of word - Pattern must have a word character at the start and a word boundary at the end * `6`: Unix shell-style wildcards - Pattern uses Unix shell wildcards (`*`, `?`, `[]`, etc.)
Comments can be added before entries to provide descriptions. A comment is preceded by a `#` (hash sign) and applies to the next entry line that appears after it.

##### Examples

    # Expand NVDA acronym
    NVDA	NonVisual Desktop Access	1	2

This means that the word "NVDA" (case sensitive, whole word) should be spoken as "NonVisual Desktop Access".

    # Convert percentages to spoken format
    (\d+)%	\1 percent	0	1

This uses a regular expression to match numbers followed by a percent sign and replaces them with the number followed by the word "percent". For example, "50%" becomes "50 percent".

    # Change "LOL" to full phrase
    LOL	laughing out loud	0	2

This means that the word "LOL" (case insensitive, whole word) should be spoken as "laughing out loud".

    # Match any .txt file using wildcards
    *.txt	text file	0	6

This uses Unix shell-style wildcards to match any string ending in ".txt" and replaces it with "text file".

For more information on speech dictionaries, refer to the [User Guide](https://download.nvaccess.org/documentation/userGuide.html#SpeechDictionaries).

## The NVDA developer guide: Plugins

### the App Module SleepMode variable

App Modules have one very useful property called "sleepMode", which if set to true almost completely disables NVDA within that application. Sleep Mode is very useful for self voicing applications that have their own screen reading functionality, or perhaps even some games that need full use of the keyboard.

Although sleep mode can be toggled on and off by the user with the key command NVDA+shift+s, a developer can choose to have sleep mode enabled by default for an application. This is done by providing an App Module for that application which simply sets sleepMode to True in the AppModule class.

### App modules for hosted apps

Some executables host various apps inside or are employed by an app to display their interfaces. These include `javaw.exe` for running various Java programs, `wwahost.exe` for some web-based apps, and `msedgewebview2.exe` for displaying web-like interfaces on apps employing Edge WebView2 runtime.

If an app runs inside a host executable or employs a different app to display the interface, the name of the app module must be the name as defined by the host or the interface executable, which can be found through the `AppModule.appName` property. For example, an app module for a Java app named "`test`" hosted inside `javaw.exe` must be named `test.py`. For apps hosted inside `wwahost`, not only must the app module name be the name of the loaded app, but the app module must subclass the app module class found in `wwahost`. By default, apps employing Edge WebView2 such as modern Outlook (olk.exe) are displayed as a webpage.

### Associating App Modules with an executable

As explained above, sometimes the default way of associating an App Module with an application is not flexible enough. Examples include:

- You want to use a single App Module for various binaries (perhaps both stable and preview versions of the application should have the same accessibility enhancements)
- The executable file is named in a way which conflicts with the Python naming rules. i.e. for an application named "time", naming the App Module "time.py" would conflict with the built-in module from the standard library
In such cases you can distribute a small global plugin along with your App Module which maps it to the executable. For example to map the App Module named "time_app_mod" to the "time" executable the plugin may be written as follows:

    import appModuleHandler
    import globalPluginHandler

    class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    	def __init__(self, *args, **kwargs):
    		super().__init__(*args, **kwargs)
    		appModuleHandler.registerExecutableWithAppModule("time", "time_app_mod")

    	def terminate(self, *args, **kwargs):
    		super().terminate(*args, **kwargs)
    		appModuleHandler.unregisterExecutable("time")

### Basics of a Global Plugin

Global Plugin files have a .py extension, and should have a short unique name which identifies what they do.

Global plugin files must be placed in the globalPlugins subdirectory of an add-on, or of the scratchpad directory of the NVDA user configuration directory.

Global Plugins must define a class called GlobalPlugin, which inherits from globalPluginHandler.GlobalPlugin. This class can then define event and script methods, gesture bindings and other code. This will all be covered in depth later.

NVDA loads all global plugins as soon as it starts, and unloads them on exit.

### Basics of an App Module

App Module files have a .py extension, and in most cases should be named the same as either the main executable of the application for which you wish them to be used or the package inside a host executable. For example, an App Module for notepad would be called notepad.py, as notepad's main executable is called notepad.exe. To map a single App Module for multiple executables, or handle when an executable name violates the Python import rules, refer to Associating App Modules with an executable. For apps hosted inside host executables, see the section on app modules for hosted apps.

App Module files must be placed in the appModules subdirectory of an add-on, or of the scratchpad directory of the NVDA user configuration directory.

App Modules must define a class called AppModule, which inherits from appModuleHandler.AppModule. This class can then define event and script methods, gesture bindings and other code. This will all be covered in depth later.

NVDA loads an App Module for an application as soon as it notices the application is running. The App Module is unloaded once the application is closed or when NVDA is exiting.

### Events (The NVDA developer guide: Plugins)

When NVDA detects particular toolkit, API or Operating System events, it abstracts these and fires its own internal events on plugins and NVDA Objects.

Although most events are related to a specific NVDA Object (e.g. name change, gain focus, state change, etc.), these events can be handled at various levels. When an event is handled, it is stopped from going further down the chain. However, code inside the event can choose to propagate it further if needed.

The order of levels through which the event passes until an event method is found is:

- Loaded Global Plugins
- The App Module associated with the NVDA Object on which the event was fired
- The Tree Interceptor (if any) associated with the NVDAObject on which the event was fired
- the NVDAObject itself.
Events are Python instance methods, with a name starting with "event_" followed by the actual name of the event (e.g. gainFocus).

These event methods take slightly different arguments depending at what level they are defined.

If an event for an NVDA Object is defined on an NVDA Object itself, the method only takes one mandatory argument which is the 'self' argument; i.e. the NVDA Object instance). Some events may take extra arguments, though this is quite rare.

If an event for an NVDA Object is defined on a Global Plugin, App Module or Tree Interceptor, the event takes the following arguments:

- self: the instance of the Global Plugin, App Module or Tree Interceptor
- obj: the NVDA Object on which the event was fired
- nextHandler: a function that when called will propagate the event further down the chain.
Some common NVDA Object events are:

- foreground: this NVDA Object has become the new foreground object; i.e. active top-level object
- gainFocus
- focusEntered: Focus has moved inside this object; i.e. it is an ancestor of the focus object
- loseFocus
- nameChange
- valueChange
- stateChange
- caret: when the caret (insertion point) within this NVDA Object moves
- locationChange: physical screen location changes
There are many other events, though those listed above are usually the most useful.

For an example of an event handled by an App Module, please refer to example 1 (focus beeps in notepad).

### Example 1: An App Module that Beeps on Focus Change Events

The following example App Module makes NVDA beep each time the focus changes within the notepad application. This example shows you the basic layout of an App Module.

Copy and paste the code between (but not including) the start and end markers into a new text file called notepad.py, which should be saved in the AppModules subdirectory. Be very careful to keep all tabs and spaces intact.

Once saved in the correct location, either restart NVDA or choose Reload Plugins found under Tools in the NVDA menu.

Finally, open Notepad and move the focus around the application; e.g. move along the menu bar, open some dialog boxes, etc. You should hear beeps each time the focus changes. Note though that if you move outside of Notepad - for instance, to Windows Explorer - you do not hear beeps.

    # Notepad App Module for NVDA
    # Developer guide example 1

    import appModuleHandler

    class AppModule(appModuleHandler.AppModule):

    	def event_gainFocus(self, obj, nextHandler):
    		import tones
    		tones.beep(550, 50)
    		nextHandler()

This App Module file starts with two comment lines, which describe what the file is for.

It then imports the appModuleHandler module, so that the App Module then has access to the base AppModule class.

Next, it defines a class called AppModule, which is inherited from appModuleHandler.AppModule.

Inside this class, it defines 1 or more events, scripts or gesture bindings. In this example, it defines one event method for gainFocus events (event_gainFocus), which plays a short beep each time it is executed. The implementation of this event is not important for the purposes of this example. The most important part is the class itself. Events will be covered in greater detail later.

As with other examples in this guide, remember to delete the created app module when you are finished testing and then restart NVDA or reload plugins, so that original functionality is restored.

### Example 2: an app module for an app hosted by wwahost.exe

The following example is the same as the Notepad app module above, except this is for an app hosted by `wwahost.exe`.

    # wwahost/test App Module for NVDA
    # Developer guide example 2

    from nvdaBuiltin.appModules.wwahost import *

    class AppModule(AppModule):

    	def event_gainFocus(self, obj, nextHandler):
    		import tones
    		tones.beep(550, 50)
    		nextHandler()

The biggest difference from the Notepad app module is where the `wwahost` app module comes from. As a built-in app module, `wwahost` can be imported from `nvdaBuiltin.appModules`.

Another difference is how the app module class is defined. As wwahost app module provides necessary infrastructure for apps hosted inside, you just need to subclass the wwahost AppModule class.

### Example 3: a Global Plugin Providing a Script to Announce the NVDA Version

The following example Global Plugin Allows you to press NVDA+shift+v while anywhere in the Operating System to find out NVDA's version. This example is only to show you the basic layout of a Global Plugin.

Copy and paste the code between (but not including) the start and end markers into a new text file with a name of example2.py, which should be saved in the globalPlugins subdirectory. Be very careful to keep all tabs and spaces intact.

Once saved in the right place, either restart NVDA or choose Reload Plugins found under Tools in the NVDA menu.

From anywhere, you can now press `NVDA+shift+v` to have NVDA's version spoken and brailled.

    # Version announcement plugin for NVDA
    # Developer guide example 3

    import globalPluginHandler
    from scriptHandler import script
    import ui
    import buildVersion

    class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    	@script(gesture="kb:NVDA+shift+v")
    	def script_announceNVDAVersion(self, gesture):
    		ui.message(buildVersion.version)

This Global Plugin file starts with two comment lines, which describe what the file is for.

It then imports the globalPluginHandler module, so that the Global Plugin has access to the base GlobalPlugin class.

It also imports a few other modules, namely ui, buildVersion and scriptHandler, which this specific plugin needs in order for it to perform the necessary actions to announce the version.

Next, it defines a class called GlobalPlugin, which is inherited from globalPluginHandler.GlobalPlugin.

Inside this class, it defines 1 or more events, scripts or gesture bindings. In this example, it defines a script method that performs the version announcement. The script decorator from the scriptHandler module is used to assign the NVDA+shift+v shortcut to this script. However, the details of the script and its binding are not important for the purposes of this example. The most important part is the class itself. More information about scripts and the script decorator can be found in the Defining script properties section of this guide.

As with other examples in this guide, remember to delete the created Global Plugin when finished testing and then restart NVDA or reload plugins, so that original functionality is restored.

### Example 3: an app module for an app employing Edge WebView2 ( msedgewebview2.exe )

The following example is an app module employing Edge WebView2 runtime with browse mode disabled by default, using modern Outlook (olk.exe) as an example.

    # msedgewebview2 example (modern Outlook/olk.py)

    import appModuleHandler

    class AppModule(appModuleHandler.AppModule):
    	disableBrowseModeByDefault: bool = True

Browse mode is disabled for this example because apps employing WebView2 display their interfaces as webpages. You can remove the "disableBrowseModeByDefault" line if you would like to let users navigate the app using browse mode commands.

### Example 4: A Global Plugin to Find out Window Class and Control ID

The following Global Plugin allows you to press NVDA+leftArrow to have the window class of the current focus announced, and NVDA+rightArrow to have the window control ID of the current focus announced. This example shows you how to define one or more scripts and gesture bindings on a class such as an App Module, Global Plugin or NVDA Object.

Copy and paste the code between (but not including) the start and end markers into a new text file with a name of example3.py, which should be saved in the globalPlugins subdirectory. Be very careful to keep all tabs and spaces intact.

Once saved in the right place, either restart NVDA or choose Reload Plugins found under Tools in the NVDA menu.

    #Window utility scripts for NVDA
    #Developer guide example 4

    import globalPluginHandler
    from scriptHandler import script
    import ui
    import api

    class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    	@script(
    		description=_("Announces the window class name of the current focus object"),
    		gesture="kb:NVDA+leftArrow"
    	)
    	def script_announceWindowClassName(self, gesture):
    		focusObj = api.getFocusObject()
    		name = focusObj.name
    		windowClassName = focusObj.windowClassName
    		ui.message(f"class for {name} window: {windowClassName}")

    	@script(
    		description=_("Announces the window control ID of the current focus object"),
    		gesture="kb:NVDA+rightArrow"
    	)
    	def script_announceWindowControlID(self, gesture):
    		focusObj = api.getFocusObject()
    		name = focusObj.name
    		windowControlID = focusObj.windowControlID
    		ui.message(f"Control ID for {name} window: {windowControlID}")

### Example 5: A Sleep Mode App Module

The following code can be copied and pasted in to a text file, then saved in the `appModules` directory with the name of the application you wish to enable sleep mode for. As always, the file must have a `.py` extension.

    import appModuleHandler

    class AppModule(appModuleHandler.AppModule):

    	sleepMode = True

### Example 6: Command to Retrieve the Length of Text in an Edit Field Using a Custom NVDA Object

This app module for notepad provides a command to report the number of characters in edit fields. You can activate it using `NVDA+l`. Notice that the command is specific to edit fields; i.e. it only works while you are focused in an edit field, rather than anywhere in the application.

The following code can be copied and pasted in to a text file, then saved in the `appModules` directory with the name of `notepad.py`.

    import appModuleHandler
    from scriptHandler import script
    from NVDAObjects.IAccessible import IAccessible
    import controlTypes
    import ui

    class AppModule(appModuleHandler.AppModule):

    	def chooseNVDAObjectOverlayClasses(self, obj, clsList):
    		if obj.windowClassName == "Edit" and obj.role == controlTypes.Role.EDITABLETEXT:
    			clsList.insert(0, EnhancedEditField)

    class EnhancedEditField(IAccessible):

    	@script(gesture="kb:NVDA+l")
    	def script_reportLength(self, gesture):
    		ui.message(f"{len(self.value)}")

### Example 7: Labelling the Notepad Edit Field Using event_NVDAObject_init

This app module for notepad makes NVDA report Notepad's main edit field as having a name of "content". That is, when it receives focus, NVDA will say "Content edit".

The following code can be copied and pasted in to a text file, then saved in the `appModules` directory with the name of `notepad.py`.

    import appModuleHandler
    from NVDAObjects.window import Window

    class AppModule(appModuleHandler.AppModule):

    	def event_NVDAObject_init(self, obj):
    		if isinstance(obj, Window) and obj.windowClassName == "Edit" and obj.windowControlID == 15:
    			obj.name = "Content"

### Making Small Changes to an NVDA Object in App Modules

Sometimes, you may wish to make only small changes to an NVDA Object in an application, such as overriding its name or role. In these cases, you don't need the full power of a custom NVDA Object class. To do this, you can use the `NVDAObject_init` event available only on App Modules.

The `event_NVDAObject_init` method takes two arguments:

- `self`: the AppModule instance.
- `obj`: the `NVDAObject` being initialized.
Inside this method, you can check whether this object is relevant and then override properties accordingly.

### NVDA Objects

NVDA represents controls and other GUI elements as NVDA Objects. These NVDA Objects contain standardised properties, such as name, role, value, states and description, which allow other parts of NVDA to query or present information about a control in a generalised way. For example, the OK button in a dialog would be represented as an NVDA Object with a name of "OK" and a role of button. Similarly, a checkbox with a label of "I agree" would have a name of "I agree", a role of checkbox, and if currently checked, a state of checked.

As there are many different GUI Toolkits and platform and accessibility APIs, NVDA Objects abstract these differences into a standard form that NVDA can use, regardless of the toolkit or API a particular control is made with. For example, the Ok button just discussed could be a widget in a Java application, an MSAA object, an IAccessible2 object or a UI Automation element.

NVDA Objects have many properties. Some of the most useful are:

- name: the label of the control.
- role: one of the Role.* constants from NVDA's controlTypes module. Button, dialog, editableText, window and checkbox are examples of roles.
- states: a set of 0 or more of the State.* constants from NVDA's controlTypes module. Focusable, focused, selected, selectable, expanded, collapsed and checked are some examples of states.
- value: the value of the control; e.g. the percentage of a scroll bar or the current setting of a combo box.
- description: a sentence or two describing what the control does (usually the same as its tooltip).
- location: the object's left, top, width and height positions in screen coordinates.
- parent: this object's parent object. For example, a list item object's parent would be the list containing it.
- next: the object directly after this one on the same level in logical order. For example, a menu item NVDA Object's next object is most likely another menu item within the same menu.
- previous: like next but in reverse.
- firstChild: the first direct child object of this object. For example, a list's first child would be the first list item.
- lastChild: the last direct child of this object.
- children: a list of all the direct children of this object; e.g. all the menu items in a menu.
There are also a few simplified navigation properties such as simpleParent, simpleNext, simpleFirstChild and simpleLastChild. These are like their respective navigation properties described above, but NVDA filters out useless objects. These properties are used when NVDA's simple review mode is turned on, which is the default. These simple properties may be easier to use, but the real navigation properties more closely reflect the underlying Operating System structure. Also, these may change in future versions of NVDA as improvements are made to simple review, so they should generally be avoided when programmatically locating specific objects.

When developing plugins, most of the time, it is not important what toolkit or API backs an NVDA Object, as the plugin will usually only access standard properties such as name, role and value. However, as plugins become more advanced, it is certainly possible to delve deeper into NVDA Objects to find out toolkit or API specific information if required.

Plugins make use of NVDA Objects in three particular ways:

- Most events that plugins receive take an argument which is the NVDA Object on which the event occurred. For example, event_gainFocus takes the NVDA Object that represents the control gaining focus.
- Scripts, events or other code may fetch objects of interest such as the NVDA Object with focus, NVDA's current navigator object, or perhaps the Desktop NVDA Object. The code may then retrieve information from that object or perhaps even retrieve another object related to it (e.g. its parent, first child, etc.).
- the Plugin may define its own custom NVDA Object classes which will be used to wrap a specific control to give it extra functionality, mutate its properties, etc.
Just like App Modules and Global Plugins, NVDA Objects can also define events, scripts and gesture bindings.

### Overview

Plugins allow you to customize the way NVDA behaves overall or within a particular application. They are able to:

- Respond to particular events such as focus and object property changes; e.g. when a control changes its name.
- Implement commands which are bound to particular key presses or other input.
- Customise the behaviour of and implement additional functionality for particular controls.
- Customise or add new support for text content and complex documents.
This section provides an introduction to developing plugins. Developers should consult the code documentation for a complete reference.

### Parsing additional command line arguments in your plugin

By default NVDA accepts a limited set of command line arguments and shows an error for unknown ones. However, if you want to use any additional arguments, this is possible by adding a handler to the extension point `addonHandler.isCLIParamKnown`. Note that since command line arguments are processed just after NVDA starts, your add-on needs to process them in a global plugin, since app modules or other drivers may not be loaded at this stage. A sample handler can be written as follows:

    def processArgs(cliArgument: str) -> bool:
    	if cliArgument == "--enable-addon-feature":
    		# Code to process your argument...
    		return True  # Argument is known to the add-on and should not be flagged by NVDA
    	return False  # unknown argument - NVDA should warn user

Then the handler needs to be registered, preferably in the constructor of your global plugin:

    import addonHandler

    class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    	def __init__(self) -> None:
    		super().__init__()
    		addonHandler.isCLIParamKnown.register(processArgs)

### Providing Custom NVDA Object Classes

Providing custom NVDA Object classes is probably the most powerful and useful way to improve the experience of an application in an NVDA plugin. This method allows you to place all the needed logic for a particular control altogether in one NVDA Object class for that control, rather than scattering code for many controls across a plugin's events.

There are two steps to providing a custom NVDA Object class:

- Define the NVDA Object class and its events, scripts, gesture bindings and overridden properties.
- Tell NVDA to use this NVDA Object class in specific situations by handling it in the plugin's `chooseNVDAObjectOverlayClasses` method.
When defining a custom NVDAObject class, you have many NVDAObject base classes to choose from. These base classes contain the base support for the particular accessibility or OS API underlying the control, such as win32, MSAA or Java access Bridge. You should usually inherit your custom NVDAObject class from the highest base class you need in order to choose your class in the first place. For example, if you choose to use your custom NVDAObject class when the window class name is "Edit" and the window control ID is 15, you should probably inherit from `NVDAObjects.window.Window`, as you are clearly aware that this is a Window object. Similarly, if you match on MSAA's `accRole` property, you would probably need to inherit from `NVDAObjects.IAccessible.IAccessible`. You should also consider what properties you are going to override on the custom NVDA Object. For instance, if you are going to override an IAccessible specific property, such as `shouldAllowIAccessibleFocusEvent`, then you need to inherit from `NVDAObjects.IAccessible.IAccessible`.

The `chooseNVDAObjectOverlayClasses` method can be implemented on app modules or global plugin classes. It takes 3 arguments:

- `self`: the app module or global plugin instance.
- `obj`: the `NVDAObject` for which classes are being chosen.
- `clsList`: a Python list of `NVDAObject` classes that will be used for `obj`.
Inside this method, you should decide which custom NVDA Object class(es) (if any) this NVDA Object should use by checking its properties, etc. If a custom class should be used, it must be inserted into the class list, usually at the beginning. You can also remove classes chosen by NVDA from the class list, although this is rarely required.

### Scripts and Gesture Bindings

App Modules, Global Plugins and NVDA Objects can define special methods which can be bound to a particular piece of input such as a key press. NVDA refers to these methods as scripts.

A script is a standard Python instance method with a name starting with "script_"; e.g. "script_sayDateTime".

A script method takes two arguments:

- self: a reference to the App Module, Global Plugin or NVDA Object instance the script was called on.
- gesture: an Input Gesture object, which represents the input that caused the script to run.
As well as the actual script method, some form of gesture binding must be defined, so that NVDA knows what input should execute the script.

A gesture identifier string is a simple string representation of a piece of input. It consists of a two letter character code denoting the source of the input, an optional device in brackets, a colon (:) and one or more names separated by a plus (+) denoting the actual keys or input values.

Some examples of gesture string identifiers are:

- "kb:NVDA+shift+v"
- "br(freedomScientific):leftWizWheelUp"
- "br(alva.BC640):t3"
- "kb(laptop):NVDA+t"
Currently, the input sources in NVDA are:

- kb: system keyboard input
- br: braille display controls
- ts: touch screen
- bk: braille keyboard input
When NVDA receives input, it looks for a matching gesture binding in a particular order. Once a gesture binding is found, the script is executed and no further bindings are used, nor is that particular gesture passed on automatically to the Operating System.

The order for gesture binding lookup is:

- The user specific gesture map
- The locale specific gesture map
- The braille display driver specific gesture map
- Loaded Global Plugins
- App Module of the active application
- Tree Interceptor of the NVDA Object with focus if any; e.g. a virtualBuffer
- NVDA Object with focus
- Global Commands (built in commands like quitting NVDA, object navigation commands, etc.)

#### Defining script properties

For NVDA 2018.3 and above, the recommended way to set script properties is by means of the so called script decorator. In short, a decorator is a function that modifies the behavior of a particular function or method. The script decorator modifies the script in such a way that it will be properly bound to the desired gestures. Furthermore, it ensures that the script is listed with the description you specify, and that it is categorised under the desired category in the input gestures dialog.

In order for you to use the `script` decorator, you will have to import it from the `scriptHandler` module.

    from scriptHandler import script

After that, just above your script definition, add the `script` decorator, providing the desired arguments. For example:

    	@script(
    		description=_("Speaks the date and time"),
    		category=inputCore.SCRCAT_MISC,
    		gestures=["kb:NVDA+shift+t", "kb:NVDA+alt+r"]
    	)
    	def script_sayDateTime(self, gesture):

In this example, your script will be listed in the input gestures dialog under the "Miscellaneous" category. It will have the description "Speaks the date and time", and will be bound to the "NVDA+shift+t" and "NVDA+alt+r" key combinations on the keyboard.

The following keyword arguments can be used when applying the script decorator:

- description: A short, translatable string which describes the command for users. This is reported to users when in Input Help mode and shown in the input gestures dialog. The script will not appear in the Input Gestures dialog unless you specify a description.
- category: The category of the script in order for it to be grouped with other similar scripts. For example, a script in a global plugin which adds browse mode quick navigation keys may be categorized under the "Browse mode" category. The category can be set for individual scripts, but you can also set the "scriptCategory" attribute on the plugin class, which will be used for scripts which do not specify a category. There are constants for common categories prefixed with SCRCAT_ in the inputCore and globalCommands modules, which can also be specified. The script will be listed under the specified category in the Input Gestures dialog. If no category is specified, the script will be categorized under "Miscellaneous".
- gesture: A string containing a single gesture associated with this script, e.g. "kb:NVDA+shift+r".
- gestures: A string list of multiple gestures associated with this script, e.g. ["kb:NVDA+shift+r", "kb:NVDA+alt+t"]. When both gesture and gestures are specified, they are combined. Either gesture, or any item in gestures can be used to trigger the script.
- canPropagate: A boolean indicating whether this script should also apply when it belongs to a focus ancestor object. For example, this can be used when you want to specify a script on a particular foreground object, or another object in the focus ancestry which is not the current focus object. This option defaults to False.
- bypassInputHelp: A boolean indicating whether this script should run when input help is active. This option defaults to False.
- allowInSleepMode: A boolean indicating whether this script should run when sleep mode is active. This option defaults to False.
- resumeSayAllMode: The say all mode that should be resumed when active before executing this script. The constants for say all mode can be found in the CURSOR enum in speech.sayAll. If resumeSayAllMode is not specified, say all does not resume after this script.
- speakOnDemand: A boolean indicating whether this script should produce speech when called while speech mode is "on-demand". This option defaults to False.
Though the script decorator makes the script definition process a lot easier, there are more ways of binding gestures and setting script properties. For example, a special "__gestures" Python dictionary can be defined as a class variable on an App Module, Global Plugin or NVDA Object. This dictionary should contain gesture identifier strings pointing to the name of the requested script, without the "script_" prefix. You can also specify a description of the script in the method's "doc" attribute. However, beware not to include an inline docstring at the start of the method if you do not set the "doc" attribute, as it would render the description not translatable. The script decorator does not suffer from this limitation, so you are encouraged to provide inline docstrings as needed when using it. Furthermore, an alternative way of specifying the script's category is by means of setting a "category" attribute on the script method to a string containing the name of the category.

### Types of Plugins

There are two types of plugins. These are:

- App Modules: code specific to a particular application. The App Module receives all events for a particular application, even if that application is not currently active. When the application is active, any commands that the App Module has bound to key presses or other input can be executed by the user.
- Global Plugins: code global to NVDA; i.e. it is used in all applications. Global Plugins Receive all events for all controls in the Operating System. Any commands bound by a Global Plugin can be executed by the user wherever they are in the operating system, regardless of application.
If you wish to improve NVDA's access to a particular application, it is most likely you will want to write an App Module. In contrast, if you wish to add some overall functionality to NVDA (e.g. a script that announces current Wireless network strength while in any application), then a Global Plugin is what you want.

Both App Modules and Global Plugins share a common look and feel. They are both Python source files (with a .py extension), they both define a special class containing all events, scripts and bindings, and they both may define custom classes to access controls, text content and complex documents. However, they do differ in some ways.

Custom appModules and globalPlugins can be packaged into NVDA add-ons. This allows easy distribution, and provides a safe way for the user to install and uninstall the custom code. Please refer to the Add-ons section later on in this document.

In order to test the code while developing, you can place it in a special 'scratchpad' directory in your NVDA user configuration directory. You will also need to configure NVDA to enable loading of custom code from the Developer Scratchpad Directory, by enabling this in the Advanced category of NVDA's Settings dialog. The Advanced category also contains a button to easily open the Developer Scratchpad directory if enabled.

The following few sections will talk separately about App Modules and Global Plugins. After this point, discussion is again more general.

## The NVDA developer guide: Remote Python Console

### Remote Python Console

A remote Python console is available in source builds of NVDA, for situations where remote debugging of NVDA is useful. It is similar to the local Python console discussed above, but is accessed via TCP.

Please be aware that this is a huge security risk. It is not available in binary builds distributed by NV Access, and You should only enable it if you are connected to trusted networks.

### Usage (The NVDA developer guide: Remote Python Console)

To enable the remote Python console, use the local Python console to import remotePythonConsole and call remotePythonConsole.initialize(). You can then connect to it via TCP port 6832.

History of previously entered lines is not supported.

The namespace is the same as the namespace in the local Python console.

There are some special functions:

- snap(): Takes a snapshot of the current state of NVDA and saves it in the snapshot variables.
- rmSnap(): Removes all snapshot variables.

## The NVDA developer guide: Translation

### Character Descriptions

Sometimes it can be very difficult or even impossible to distinguish one character from another. For example, two characters might be pronounced the same way, even though they are actually different characters. To help users when this occurs, character descriptions can be provided which describe the character in a unique way.

Character descriptions can be provided for a locale in a file named `characterDescriptions.dic` in the directory for the locale. This is a UTF-8 encoded text file. Blank lines and lines beginning with a "`#`" character are ignored. All other lines should contain a character, followed by a tab, then one or more descriptions separated by tabs. Multiple descriptions for a character will be read with natural pauses between them when reading a single character, e.g. when using `leftArrow` or `rightArrow`. When reading character descriptions of multiple subsequent characters using spelling commands, the first description is used for each character, e.g. spelling the current line with triple press on `NVDA+upArrow`.

For example:

    # This is a comment.
    a	alpha
    b	bravo beta

In this example, "a" will read "alpha" as the character description, and "b" will read as "bravo, beta".

In most cases, the characters in this file should be a single lower case character. It is assumed that characters will have the same description regardless of their case, so upper case characters are converted to lower case before looking up their character descriptions.

#### Translating this file

Translation of `characterDescriptions.dic` happens via [Pull Request to NVDA](https://github.com/nvaccess/nvda/blob/master/projectDocs/translating/github.md).

For a full example and reference, please look at [the English `characterDescriptions.dic` file](https://github.com/nvaccess/nvda/blob/master/source/locale/en/characterDescriptions.dic).

### Gestures

The gestures defined originally in NVDA are configured to expect English software and keyboard layout. In most cases, these gestures can also be executed on other keyboard layouts without any problem. However, sometimes a gesture originally defined by NVDA is not suitable for a specific locale (keyboard layout or software). The need to modify an original gesture may be due to the following reasons:

- The original gesture is defined with a character that is not a key name on the locale keyboard layout. Generally, the key names are the characters that can be input without the help of a modifier key (`shift`, `control`, etc.)
- The original gesture takes advantage of the key's physical location on the English keyboard layout, but this advantage does not exist with the locale keyboard layout.
- The original gesture is defined to match a native shortcut in Windows or in an application, but the shortcut in the local version of Windows or of this application is not the same as the English one.
In all of these cases, NVDA allows remapping of this gesture for this specific locale.

#### Examples

Below are three detailed examples of `gestures.ini` files corresponding to the three listed situations where a gesture remapping could be required.

##### Example 1: The original gesture is defined with a character that is not a key name on the locale keyboard layout

In the original English version, the scripts for left and right mouse click (laptop layout) are executed with `NVDA+[` and `NVDA+]`, respectively.

- On an English keyboard layout, the `[` and `]` keys are the two keys to the right of the `p` key.
- On an Italian keyboard layout, `[` and `]` characters can only be input with the help of the `altGr` modifier: `altGr+è` and `altGr+plus`, respectively.
Thus, the Italian translators decided to remap these scripts using the two keys at the right of the `p` key on the Italian keyboard layout, i.e. `è` and `+`. To do this, they have added the following lines in the `gestures.ini` file:

    [globalCommands.GlobalCommands]
    	leftMouseClick = kb(laptop):NVDA+è
    	rightMouseClick = kb(laptop):NVDA+plus

##### Example 2: The original gesture takes advantage of the keys physical location

Looking again at the scripts for left and right mouse click (laptop layout) we can see that they are originally mapped (in English) to two neighboring keys. This corresponds to the left and right buttons of the mouse. As seen in example 1, many translators have had to modify these keys. Most of them (if not all) have chosen two neighboring keys. For example, in the French `gestures.ini`, the following lines have been added:

    [globalCommands.GlobalCommands]
    	None = kb(laptop):nvda+[, kb(laptop):nvda+control+[, kb(laptop):nvda+], kb(laptop):nvda+control+], kb(laptop):nvda+shift+., kb(laptop):nvda+., kb(laptop):nvda+control+.
    	leftMouseClick = kb(laptop):nvda+ù
    	rightMouseClick = kb(laptop):nvda+*

The `ù` and `*` on the French layout are not at the same location as `[` and `]` of the English layout, but these are still two neighboring keys. Moreover we can see here that `NVDA+[` and `NVDA+]`, among others, have been mapped to `None`, in order to unbind these gestures. For the French (France) layout, this was not mandatory since there is no possibility to input `NVDA+[` or `NVDA+]` without any other modifier key.

##### Example 3: The original gesture is defined to match a native shortcut

NVDA provides a script for the Word document object named `toggleBold`. This script is mapped to the same gesture as the Word native shortcut to set text bold, i.e. `control+b` in the English version of Word. However in the French version of Word, the shortcut to turn text bold is `control+g`. The G stands for "gras" meaning "bold" in French. The following lines have been added in the French `gestures.ini` file to remap this script:

    [NVDAObjects.window.winword.WordDocument]
    	None = kb:control+b, kb:control+[, kb:control+], "kb:control+shift+,", kb:control+shift+., kb:control+l, kb:control+r
    	toggleBold = kb:control+g, kb:control+shift+b

We can see that `control+b` has been unbound. This was necessary because it is the shortcut of another command in the French version of Word. No remapping has been done for the `toggleItalic` script, since the shortcut is the same for French and English versions of Word.

#### How to remap a shortcut key

##### Identify the class, the script and the original gesture to be remapped

To edit the `gesture.ini` file, you will have to identify the class, the script and the original shortcut you want to remap.

##### Case of a global command script

If the gesture to be remapped is a global command, you may execute the following steps to find out the class and the script name of the command:

- activate input help (`NVDA+1`)
- press the gesture you want to remap, e.g. `NVDA+]` (laptop layout)
- de-activate input help (`NVDA+1`)
- open the log (`NVDA+F1`)
- find the line corresponding to the moment you executed the gesture, e.g.:

    Input help: gesture kb(laptop):NVDA+], bound to script rightMouseClick on globalCommands.GlobalCommands

The information you are searching is on this line:

- script name: `rightMouseClick`
- class name: `globalCommands.GlobalCommands` (Note that this is always the class for global commands)
- original gesture: `kb(laptop):NVDA+]`

##### Case of an application specific script

In case you want to remap an application specific script, you will have to follow the same steps as those for a global command script. You just need to ensure before proceeding that you are in the targeted application.

##### Case of an object specific script

For object specific scripts such as the ones linked to `NVDAObjects.window.winword.WordDocument`, you may follow the same steps as those for application specific scripts, paying attention to the following two points:

- You need to ensure before proceeding that the object to which the script is bound is focused.
- Some of these scripts have no help message, so you may not hear anything when executing them in input help mode; but the script's name and the class of the object will still appear in the log.
Note that the class of the object appearing in the log may be a subclass of the one where the original gesture is actually bound. In this case, you will have to explore NVDA's source code to find this parent class.

#### Translating this file

Translation of `gestures.ini` happens via [Pull Request to NVDA](https://github.com/nvaccess/nvda/blob/master/projectDocs/translating/github.md).

- In this file the sections correspond to the class to which the script belongs. If the class your looking for does not exist, create this section.
- Under the targeted section, add a line corresponding to the new shortcut. e.g.:

    toggleBold = kb:control+g, kb:control+shift+b

- If a line already exists for the script name, but you want to modify the shortcut, add the new shortcut on the same line, separating each shortcut with a comma ("`,`").
- If you want to unmap the original shortcut, just map it to `None`, e.g.:

    None = kb:control+b

- Unmapping the original shortcut is only required if this shortcut does not match any other remapped locale shortcut.

### Symbol Pronunciation

It is often useful to hear punctuation and other symbols pronounced as words when reading text, particularly when moving by character. Unfortunately, the pronunciation of symbols is inconsistent between speech synthesisers and many synthesisers do not speak many symbols and/or do not allow control over what symbols are spoken. Therefore, NVDA allows information about symbol pronunciation to be provided.

This is done for a locale by providing a file named `symbols.dic` in the directory for the locale. This is a UTF-8 encoded text file. Blank lines and lines beginning with a "`#`" character are ignored. All locales implicitly inherit the symbol information for English, though any of this information can be overridden.

The file contains two sections, complex symbols and symbols.

#### Defining Complex Symbols

The first section is optional and defines regular expression patterns for complex symbols. Complex symbols are symbols which aren't simply a character or sequence of characters, but instead require a more complicated match. An example is the full stop (.) sentence ending in English. The "." is used for multiple purposes, so a more complicated check is required to determine whether this refers to the end of a sentence.

The complex symbols section begins with the line:

    complexSymbols:

Subsequent lines contain a textual identifier used to identify the symbol, a tab and the regular expression pattern for that symbol. For example:

    sentence ending	(?<=[^\s.])\.(?=[\"')\s]|$)
    dates with .	\b(\d\d)\.(\d\d)\.(\d{2}|\d{4})\b

Again, the English symbols are inherited by all other locales, so you need not include any complex symbols already defined for English.

#### Defining Symbol Information

The second section provides information about when and how to pronounce all symbols. It begins with the line:

    symbols:

Subsequent lines should contain several fields separated by tabs. The only mandatory fields are the identifier and replacement. The default will be used for omitted fields. The fields are as follows:

- `identifier`: The identifier of the symbol. In most cases, this is just the character or characters of the symbol. However, it can also be the identifier of a complex symbol. Certain characters cannot be typed into the file, so the following special sequences can be used:
    - `\0`: null
    - `\t`: tab
    - `\n`: line feed
    - `\r`: carriage return
    - `\f`: form feed
    - `\#`: # character (needed because # at the start of a line denotes a comment)
- `replacement:` The text which should be spoken for the symbol. If the symbol is a complex symbol, `\1`, `\2`, etc. can be used to refer to the groups matches, which will be inlined in the replacement, allowing for simpler rules. This also means that to get a `\` character in the replacement, one has to type `\\`.
- `level`: The symbol level at which the symbol should be spoken.
    - The symbol level is configured by the user and specifies the amount of symbols that should be spoken.
    - This field should contain one of the levels "none", "some", "most", "all" or "char", or "-" to use the default.
    - "char" means that the symbol should only be pronounced when moving by character.
    - The default is to inherit the value or "all" if there is nothing to inherit.
- `preserve`: Whether the symbol itself should be preserved to facilitate correct pronunciation by the synthesiser. For example, symbols which cause pauses or inflection (such as the comma in English) should be preserved. This field should be one of the following:
    - `never`: Never preserve the symbol.
    - `always`: Always preserve the symbol.
    - `norep`: Only preserve the symbol if it is not being replaced; i.e. the user has set symbol level lower than the level of this symbol.
    - `-`: Use the default. The default is to inherit the value or "never" if there is nothing to inherit.
Finally, a display name for the symbol can be provided in a comment after a tab at the end of the line. This will be shown to users when editing the symbol information and is especially useful for translators to define translated names for English complex symbols.

#### Examples

    (	left paren	most

This means that the "(" character should be spoken as "left paren" only when the symbol level is set to most or higher; i.e. most or all.

    ,	comma	all	always

This means that the "," character should be spoken as "comma" when the symbol level is set to all and that the character itself should always be preserved so that the synthesiser will pause appropriately.

    . sentence ending	point	# . fin de phrase

This line appears in the French symbols.dic file. It means that the ". sentence ending" complex symbol should be spoken as "point". Level and preserve are not specified, so they will be taken from English. A display name is provided so that French users will know what the symbol represents.

    dates with .	\1 point \2 point \3	all	norep	# date avec points

This line appears in the French symbols.dic file. It means that the first, second, and third groups of the match will be included, separated by the word 'point'. The effect is thus to replace the dots from the date with the word 'point'.

If your language uses a thousands separator such as a full stop (.) which is handled incorrectly due to other rules, you will need to define a complex symbol pattern for it. For example, if your language uses a comma (,) as its thousands separator, you would include the following in the complex symbols section:

    thousands separator	(?<=\d)\,(?=\d)

You would also include something like the following in the main symbols section:

    thousands separator	comma	all	norep

#### Translating this file

Translation of `symbols.dic` happens via [Pull Request to NVDA](https://github.com/nvaccess/nvda/blob/master/projectDocs/translating/github.md).

See the file [locale\en\symbols.dic](https://github.com/nvaccess/nvda/blob/master/source/locale/en/symbols.dic) for the English definitions which are inherited for all locales.

### Translation

In order to support multiple languages/locales, NVDA must be translated, and data specific to the locale must be provided. This section only includes information on custom NVDA file formats required for translation. Other items need to be translated, such as the NVDA user interface and documentation, but these use standard file formats. For complete documentation about translating NVDA, please see the [Translating page](https://github.com/nvaccess/nvda/blob/master/projectDocs/translating/readme.md)

## Miscellaneous

### Authors, Contributions, and Copyright

This guide is primarily maintained, and was originally written, by Joseph Lee ([@josephsl](https://github.com/josephsl)), and is shaped by the NVDA user and developer community. Luke Davis ([@XLTechie](https://github.com/XLTechie)) sometimes serves as editor.

Valuable contributions and corrections from the community are welcome.

NVDA is copyright 2006-2026 NV Access Limited. Microsoft Windows, Microsoft Office, Win32 API, and other Microsoft products are copyright Microsoft Corporation. IAccessible package is copyright by IBM and the Linux Foundation. Python is copyright by Python Software Foundation. Other products mentioned are copyrighted by their respective copyright holders.

### Available Add-ons

Name

Version

Channel

Publisher

2Factor Authenticator

1.5.1

stable

umesh rathore

AbsoluteFileAndFolder

2026.8.5

stable

Chai Chaimee

AbsoluteSite

2026.8.0

stable

Chai Chaimee

AbsoluteTranslate

2026.9.0

stable

Chai Chaimee

AbsoluteWindows

2026.7.7

stable

Chai Chaimee

AbsoluteYoutube

2026.8.5

stable

Chai Chaimee

Access8Math

5.0

stable

Woody Tseng

Accessible agenda

2026.05.14

stable

Rui Fontes

Accessible Bluetooth Audio Receiver

1.2.0

stable

Muhammad

Accessible Discord

1.0.8

stable

salmanf16

Accessible KBBI - Indonesian Dictionary Search

1.1

stable

Muhammad

Add-ons documentation

2026.05.07

stable

Rui Fontes

addon Store Lite

2026.8.5

stable

Chai Chaimee

Advanced NVDA Remote

1.0.0

stable

ashu-choudhury

AI assistant

0.13.1

stable

adilhusain shaikh

AI Content Describer

2026.05.06

stable

Carter Temm and other contributors

AI Email Composer Pro

2.2.0

stable

Kasturi Bhosale

AI-Hub

26.06.16

stable

AAClause

AiSound5 Chinese TTS Add-On For NVDA

2026.05

stable

NVDA Contributors

alzaker

2.0.0

stable

Ahmed Samy

AMRadio

1.6

stable

jpavonabian

Application dictionary

2026.05.11

stable

Rui Fontes

appOn

2026.7.7

stable

Chai Chaimee

Aprendizaje de Python con NVDA.

1.0

stable

Kevin Andrés Velasquez Vargas

ArubaSign - Campi firma

1.1.0

stable

Alexandru Vida

Ask OpenRouter

20260727.0.0

stable

abdel792

ATL Productivity Suite

2.0.0

stable

Accessible tech labs India

Atlas.ti Accessibility Enhancements

1.3.0

stable

Christos Bouronikos

Audio Manager

1.0.9

stable

huaiyinfeilong

Audio Switcher

2026.2

stable

kamal yaser

Audio Video Converter

2026.05.06

stable

Rainer Brell

AudioScreen

2026.3.1

stable

josephsl

AudioToggles

2.0

stable

rajath tirumangalam

Autoclip, automatically speak clipboard content when it changes

1.3.4

stable

Mazen

Automatically maximize application windows

1.1

stable

tecwindow

Banking4W - Topbanking

2026.05.02

stable

Rainer Brell

BatteryChime

1.0.1

stable

leo

Bible

2026.08.19

stable

Halimon Alexandr

Blackout - Darkens the screen except for the speech and Braille viewer

2026.05.02

stable

BFW Würzburg

Bluetooth Battery Report

0.4

stable

haitun

BOA: Better Office Accessibility

2.0.0

stable

MisterK

Braille Cell Ignorer

0.2.1

stable

cary-rowen <manchen_0528@outlook.com>

Braille Essentials

26.08

stable

josephsl

Braille Extender

26.06.16

stable

AAClause

Browse mode content first

1.1.1

stable

shenguangrong

Browser Options

1.2.2

stable

Andhi Mardianto

BrowserNav

2.7.8

stable

mltony

Calculate your BMI

2026.2.1

stable

Edilberto Fonseca

Calculator

2.2.2

stable

Andhi Mardianto

Calendário Simples BR

2026.05.03

stable

Leandro Souza

Calibre accessibility enhancements

2026.3.1

stable

Javi Dominguez

Capital Selection Indicator

0.2.2

stable

Cary-rowen <manchen_0528@outlook.com>

caption image useing local AI models

0.4.0

stable

Tianze

Char Desc Merge

1.0.1

stable

addonWorkshop

Character information

3.8

stable

Cyrille Bougot

Charging Notifier

0.2.2

stable

Cary-rowen <manchen_0528@outlook.com>

Check Input Gestures

1.1.0

stable

Oleksandr Gryshchenko

Chinese input method support for NVDA

2026.6.28

stable

Cary-rowen <manchen_0528@outlook.com>, Chenfu <394434124@qq.com>, hwf1324 <1398969445@qq.com>

Chinese-Vietnamese Gamers' Dictionary

1.0.5

stable

KtGame

CJK Enhanced User Interface

1.10

stable

Michael M Chen; Victor Cai; Woody Tseng

Clean Terminal Output

1.0

stable

Ripple Software

Clear Clipboard

1.1

stable

Hoàng Long

Clip Contents Designer

52.0.0

stable

nvdaes

Clipboard Announcer

1.3.1

stable

H2k1

Clipboard Content Editor

1.3.1

stable

Fauzan January

Clipboard Enhancement

2.9.7

stable

Cary-rowen <manchen_0528@outlook.com>

ClipboardHistory

2026.7.0

stable

Chai Chaimee

Clipspeak

2026.08.24

stable

Rui Batista

Clock

20260521.0.0

stable

abdel792, zstanecic

Cloud Uploader

4.25.2

stable

Naday

CMDReader

2026.8.8

stable

Chai Chaimee

Color Contrast Checker for NVDA

2026.06.12

stable

Carter Temm <cartertemm@gmail.com>

Columns Review

5.7.0

stable

Alberto Buffolino

Command Helper

2026.2.0

stable

Javi Dominguez

Command runner for NVDA input gesture dialog

0.2.0

stable

Çağrı Doğan <cagrid@hotmail.com>

Console Toolkit

1.4.8

stable

Tony Malykh

Contacts Manager for NVDA

2026.2.2

stable

Edilberto Fonseca

Content priority reading

0.3

stable

lamb

Control Usage Assistant

20260826.0.0

stable

nvdaes

Count elements of the selected text

2026.05.15

stable

Rui Fontes

Currency converter

1.2.1

stable

Arash

Currency converter

3.0

stable

Mister Anas

Cursor Locator

21.0.0

stable

nvdaes

Custom App Modules Mapper

1.0.0

stable

Marlon Brandão de Sousa

Custom Browse Mode

7.0.0

stable

nvdaes

Custom Labels

2026.1

stable

Kefas Lungu

Custom Notifications

15.0.0

stable

nvdaes

Day of the week

20260727.0.0

stable

abdel792

DBeaver Eclipse NVDA

2026.1.0

stable

Jean Braz

Dengjen Neural Voices

4.0.1

stable

Ali Ustek

Detailed Element Info

1.0.2

stable

Mustafa Elçiçek

Dictionaries

2026.05.10

stable

Rui Fontes

DictionaryDisplayLite

2026.8.5

stable

Chai Chaimee

Discord Message Hotkeys

0.9.0

stable

Leos

DoctorNVDA

2026.9.0

stable

Chai Chaimee

Document Formatting Rotor

1.2

stable

Derek Riemer <driemer.riemer@gmail.com>

Document reader for NVDA

1.0

stable

Sujan Rai

DragHelper

1.0.1

stable

LUCA

Dropbox

2026.05.10

stable

Rui Fontes

Earcons and speech rules

3.0.7

stable

mltony

Easy Table Copy

2026.7.0

stable

Çağrı Doğan <cagrid@hotmail.com>

Easy Table Navigator

2.7.1

stable

Corentin Bacqué-Cazenave

easyNavigation

2026.2.0

stable

Javi Dominguez

EDICO Scientific Editor

2026.1

stable

Alberto Zanella

Emoticons

38.0.0

stable

nvdaes

eMule

26.0.0

stable

nvdaes

En Dash Bash

1.0.2

stable

Bill Dengler

Engelsiz Mail

1.8.2

stable

Mehmet Aykurt

Engelsiz Nota

1.2.0

stable

Mehmet Aykurt

Enhanced Annotations

23.0.0

stable

nvdaes

Enhanced Clipboard Reading

3.0

stable

Nikola Jović

Enhanced Control Support

1.2.2

stable

Emil-18

Enhanced dictionaries processing for NVDA

1.7.1

stable

Marlon Brandão de Sousa

Enhanced Duck

0.1.1

stable

Prateek Kumar

Enhanced find dialog for NVDA

1.9.0

stable

Marlon Sousa, Thiago Seus

Enhanced Language Detection

1.2.5

stable

Emil-18

Enhanced Object Navigation

0.3.2

stable

Emil-18

Enhanced Symbol Cycler

1.0.0

stable

JasperLee

Enhanced Touch Gestures

26.09

stable

josephsl

Event Tracker

26.3.3

stable

josephsl

FastRead

1.0.4

stable

Andre Louis

Favorite folders and files - Register favorite folders and files

2026.05.22

stable

Rui Fontes

Favorite links

2026.2.1

stable

Edilberto Fonseca

fenCodeReader

2026.2.1

stable

Javi Dominguez

FileZilla

2026.05.10

stable

Nael Sayegh

freeRadio

2026.23.3

stable

Çağrı Doğan <cagrid@hotmail.com>

Game Mode

2026.8.1

stable

福恩

Gamepad Support

2026.5

stable

Shunxian Wu

gestureDuplicate

2026.5.1

stable

Chai Chaimee

GETEM E-Kütüphane

1.2.1

stable

Mehmet Aykurt

Global Sonic Pitch

1.1.8

stable

Kazimierz Parzych, DJ Graco

Golden Cursor

26.1

stable

jmdaweb

GoldWave

26.09

stable

josephsl

Google Docs accessibility

1.4.3

stable

mltony

Greek Math Reader

2.0.0

stable

Bouronikos Christos

Ham Calls

0.2.1

stable

Stephen Clower

HardSub Reader

1.3.0

stable

Shaima Almarzooqi

Hear2Read Indic Speech Synthesizer

2.0.8

stable

Hear2Read

Hearthstone Card Lookup

1.0.0

stable

Samuel Kacer

hijri date

1.0.3

stable

Mister Anas

IndentNav

2.2.9

stable

mltony

Informações da rede

2.1.1

stable

francisco figueiredo

Input lock

26.1

stable

jmdaweb

instant Access

2026.4

stable

kamal yaser

Instant Translate

5.1.1

stable

addonFactory

IntelliJ Improved

1.6.0

stable

Samuel Kacer

Internet Status

2026.1

stable

hamidrehzaey

invisible Browser Dictionary

2026.5.3

stable

Chai Chaimee

invisinote

1.7

stable

ClippyCat

Islamic Pedia

1.2.0

stable

Fauzan January

Item Order Announcer

2.1

stable

Balaraz

Keep awake

2026.1.0

stable

Javi Dominguez

Kill Process

2026.5

stable

Angel Alcántar

Koruz.biz MurText mp3/mp4 convert to TXT, SRT, VTT

3.0.1

stable

Koruzbiz

Kurum Rehberi

1.2.0

stable

Mehmet Aykurt

leanCalendar

0.2.6

stable

Cary-rowen <manchen_0528@outlook.com>

LinguaPal

1.1.0

stable

Ali

Link Library

2.3.2

stable

Ibrahim Hamadeh

LION

3.3.0

stable

anmi2004

Listen

2026.8.5

stable

Chai Chaimee

logViewer

2026.7.7

stable

Chai Chaimee & Pierre-Louis R.

Lone Wolf support App Module

1.0.0

stable

Karl Eick

Macro Studio

1.0.1

stable

Bilal Uğur Özçıtak

Main Landmark Navigator

1.0.5

stable

Jan Balák

Maqamusic

3.0

stable

Riad Assoum

Markdown Navigator

0.2.7

stable

cary-rowen <manchen_0528@outlook.com>

Message Sweeper - Clean Slack & Teams messages for NVDA

1.1.0

stable

KINTO Technologies Corporation

messengerAccess

2026.6.25

stable

NVDA_TH

MetaTrader

2026.1

stable

hamidrehzaey

MicroPower DeltaTalk TTS

2026.02.11

stable

Patrick Barboza <patrickbarboza774@gmail.com>, Wendrill Aksenow Brandão <wendrillaksenow@gmail.com>

Monitoreo de batería

1.2.1

stable

Ángel Reyes

Mouse Enhancement

0.9.3

stable

hwf1324

Mozilla Apps Enhancements

2026.1.2

stable

Javi Dominguez

mp3DirectCut

20260803.0.0

stable

abdel792

Music & Lyrics Finder

0.2.0

stable

Çağrı Doğan <cagrid@hotmail.com>

Muslimku

7.1.4

stable

Dwi Citolaksono

MW-word-lexicon

2.0

stable

Abdullah Ashraf <abdullahashraf4846@gmail.com

My File Archive - Internet Archive Integration

26.8.18

stable

Mehmet Aykurt

Nao

2026.1.1

stable

Alessandro Albano, Simone Dal Maso, Davide Decarne

Native Speech Generation

1.7.0

stable

Muhammad

Navigation Sound Effects

2.2.0

stable

Ahmed Samy

Network Tools

1.0.0

stable

Guilherme Ítalo

Notepad Markdown Browse Mode

20260825.0.0

stable

abdel792

Notepad++

2026.06.1

stable

Derek Riemer <driemer.riemer@gmail.com>, Tuukka Ojala <tuukka.ojala@gmail.com>

Number Processing

1.1.0

stable

Alberto Buffolino

Numpad Nav Mode

26.2.0

stable

Luke Davis, josephsl

NVChime

2.0.1

stable

leo

NVDA BatteryReport

1.01

stable

Leo Guima

NVDA Chinese Community Update Mirror

0.7.3

stable

zh-yx, Cary-rowen, hwf1324 <support@nvdacn.com>

NVDA Coach - Interactive Screen Reader Training

1.5.7

stable

Tony Gebhard

NVDA Composer

1.6.4

stable

Andre Louis

NVDA Dev & Test Toolbox

10.1

stable

Cyrille Bougot

NVDA Macro Manager

1.2.3

stable

Muhammet Enes Şenovalı

NVDA recorder

2026.05.10

stable

Rui Fontes

NVDA SpeedTest

2.0

stable

Leo Guima

obj Watcher

1.0.7

stable

Cary-rowen <manchen_0528@outlook.com>, hwf1324 <1398969445@qq.com>

Object Boundary Feedback

0.2.1

stable

Cary-rowen <manchen_0528@outlook.com>

Object Location Tones

26.1.0

stable

Dalen

ObjPad

26.09

stable

josephsl

Open Bible

2026.08.26

stable

Leandro Souza

Open Link With

3.3.1

stable

Ibrahim Hamadeh

OpenCC Chinese Converter

2.1.0

stable

Kevin Lin <kevin82222@gmail.com>

Outlook Extended

3.4

stable

Cyrille Bougot

Page Reporter

3.1.0

stable

Rosendo Barde Hubilla Jr. and Joseph bautista

Parses and speaks date and time expressions

1.0.4

stable

Andre Louis

PC Keyboard Braille Input

51.0.0

stable

nvdaes

PC QQ Enhancement

1.2.3

stable

Cary-rowen, NVDA Chinese Community and other contributors, Original work by SmileSky<mzdk100@foxmail.com>

PC WeChat Enhancement

2.4.3

stable

Cary-Rowen <manchen_0528@outlook.com>

pcloud

0.9.1

stable

David Parduhn <xkill85@gmx.net>

Per-Application Volume Control

2026.05.241528

stable

JoaoDEVWHADS

Perky Duck

12.0.0

stable

nvdaes

Place markers

53.0.0

stable

nvdaes

Pleasant Progress Bar

0.22

stable

lamb

Polyglot

1.1.1

stable

cary-rowen <manchen_0528@outlook.com>

Pomodoros Manager

1.24

stable

jpavonabian

PPA Tatip WakeUp ตาทิพย์จงตื่น!

2026.8.1

stable

Chai Chaimee

prayer times

2.0

stable

Mister Anas

Professional Media Downloader

26.09.01

stable

Umesh Rathore

Profile Announcer

0.1.0

stable

Rahul Vaniya

Program Resource Reporter

2.3.0

stable

Justin

ProgressReader

0.4.1

stable

vbprofi

ProtonVPN Accessibility

1.1.0

stable

Mama Sene

Proxy support

26.1

stable

jmdaweb

Read Feeds

47.0.0

stable

nvdaes

Readonly Profiles

3.0.0

stable

nvdaes

Reference Tone Tuner

2026.07.06

stable

Leandro Souza

REGEX++

2026.8.8

stable

Chai Chaimee

Regists blocks of text frequently used

2026.05.10

stable

Rui Fontes

Remap Applications key

2026.05.10

stable

Rui Fontes

ReminderApp

2.8

stable

Adriano Barbieri

Remote Desktop Accessibility

1.7.1

stable

Leonard de Ruijter

Remote Speech Control

1.1.1

stable

Ed

Remote++

0.5.0

stable

Cary-rowen <manchen_0528@outlook.com>

Report Symbols

32.0.0

stable

nvdaes

Reporting the International Phonetic Alphabet in Braille

1.2.4

stable

Cary-rowen <manchen_0528@outlook.com>

Resource Monitor

26.09

stable

josephsl

Review Cursor Copier

1.9

stable

Tuukka Ojala

Review Cursor Find

1.2.2

stable

Emil-18

RHVoice

1.18.201

stable

Zvonimir Stanecic, RHVoice contributors

Ribbon Menu

1.1.0

stable

Alexandru Vida

ROB enhancements

2026.08.28

stable

Rainer Brell

Sarvam AI assistant

1.0.7

stable

Rakesh Honisty

Say control type before label

2026.07.04

stable

Pierre-Louis Renaud

Say Product Name and Version

2026.4.1

stable

Luke Davis

sayCurrentKeyboardLanguage

20260727.0.0

stable

abdel792

Scanvox for NVDA

2026.05.16

stable

Nael Sayegh

screen wrapping for nvda

26.1

stable

Hamada Trichine

screenshots wizard

2026.1.1

stable

Javi Dominguez

Search With

2.6.8

stable

Ibrahim Hamadeh

Second and minute time cues

1.0.2

stable

Andre Louis

Selector de salida de audio por aplicación

1.0.0

stable

Nicolas Alfaro

SentenceNav

2.14.2

stable

Tony Malykh

Set Character Description Delay

2026.1.1

stable

Çağrı Doğan <cagrid@hotmail.com>

ShortcutLaunch

1.0

stable

Vatsal Gautam

Show Clipboard Content

1.0

stable

Hoàng Long

Show selection when braille is tethered to review

2026.0626.0

stable

Burman's Computer and Education Ltd.

siamSquare พจนานุกรมไทย คลังคำ

2026.7.7

stable

Chai Chaimee

Simple calculator

2.2

stable

Mister Anas

Simple Timer and stopwatch for NVDA

1.7.0

stable

Marlon Brandão de Sousa

simpleCopy

2026.9.0

stable

Chai Chaimee

SiteMarker

2026.8.5

stable

Chai Chaimee

Sonata Sherpa Voices

2026.1

stable

Jim Grimsby Jr.

soundAlign

2026.8.6

stable

Chai Chaimee

soundWave: Faster-than-realtime text-to-audio renderer

1.2.8

stable

Andre Louis

specialCharacter

2026.5.3

stable

Chai Chaimee

Speech history review and copying

2026.1

stable

James Scholes

SPSS Accessibility Plugin

1.2.0

stable

Bouronikos Christos

StateBeforeLabel

2026.8.5

stable

Chai Chaimee

StationPlaylist

26.09

stable

josephsl

Stay Awake

2.0

stable

rajath tirumangalam

Studio Recorder

26.04

stable

Marco Steinebach

Subtitle reader

3.81

stable

福恩

Suno AI Prompt Oluşturucu

1.2.0

stable

Mehmet Aykurt

Suno AI Voice Assistant

2.0.3

stable

suno tech Solutions

Switch synth

1.07.0

stable

tspivey

SysTrayList

2026.08.24

stable

Rui Batista

Tabela do Brasileirão

2026.7.13

stable

Leandro Souza

Talking Meta Trader 5

2.0.0

stable

Angeliberta Software

Task Switcher

1.3.7

stable

mltony

Tele NVDA remote assistance

2026.8.17

stable

jmdaweb

Terminal Access for NVDA

2.3.0

stable

Pratik Patel

TesseractOCR: An OCR add-on

2026.06.16

stable

Rui Fontes

text information

1.6

stable

Carter Temm <cartertemm@gmail.com>

Text Marks the Spot

1.0.15

stable

Casey Mathews

text normalizer

2026.07.18

stable

alekssamos

Text snippet handling features for NVDA

1.0.11

stable

snippetsForNVDA contributors

Thunderbird+ G5.1 (TB >= 140)

2608.22.0

stable

Pierre-Louis Renaud

Tiflotecnia voices for NVDA

4.2.1

stable

Rui Fontes

TikTok Live Reader

1.8

stable

Stefan Tsvyatkov

Time Zoner

3.05

stable

Munawar Bijani

Tony's enhancements

1.22.5

stable

mltony

ToolbarsExplorer

2.0.0

stable

Alberto Buffolino

Tools for managing add-ons

2026.05.02

stable

Rui Fontes

Total Commander Extended

2026.07.01

stable

Rainer Brell

Training Keyboards Commands

3.2.8

stable

Ibrahim Hamadeh

Translate

2026.08.24

stable

Yannick Plassiard, salmanf16

UIANotificationSwitch

2026.5

stable

Shunxian Wu

Unicode Braille Input

5.0.2

stable

Leonard de Ruijter

UnigramCacheCleaner

1.5.3

stable

Ruslan Dolovaniuk

Universal focus tracker

1.5

stable

Muhimen nabeel

Universal Tuner for NVDA

2026.07.27

stable

Peem Narkkhwan

Update channel selector

26.3

stable

jmdaweb

URL Shortener

20.0.0

stable

nvdaes

uTalk

2026.7.0

stable

Chai Chaimee

v2rayN

0.8.1

stable

Mehran Latifi

Video Maker

1.0.0

stable

Kasturi Bhosale

Video ve Ses İndirici

1.2.1

stable

Fikret Uzun

virtual keyboard

2026.5

stable

Shunxian Wu

Virtual Notes For NVDA (creates virtual notes to be read by NVDA)

1.5.0

stable

Juliano Lopes

Virtual Review

2026.07.29

stable

Rui Batista

Vis Aware

0.8.1

stable

cary-rowen <manchen_0528@outlook.com>

Vision Assistant Pro

2026.08.13

stable

Mahmood Hozhabri

Visma Administration

2026.1.0

stable

Karl-Otto Rosenqvist

VLC Media Player

2026.1.2

stable

Javi Dominguez

Voice Input

1.0.2

stable

cyber zen

Voice Switcher

26.1

stable

Smart Thinh

VoiceToggle

1.7.4

stable

Adam Samec

Volume Adjustment

1.5.0

stable

Oleksandr Gryshchenko

VolumePower

2026.9.0

stable

Chai Chaimee

Voz nativa do DOSVOX

2.1.1

stable

Edson Miranda

Weather Checker

4.4.1

stable

Swarup Baral

Weather Report

1.2.0

stable

Abdulaziz

Weather_Plus

11.0

stable

Adriano Barbieri

Wenxing Braille Display

1.0.0

stable

wangru

WhatsApp Desktop accessibility enhancements

1.8.1

stable

Nuno Costa

WhatsApp Desktop Enhancer

26.8.24

stable

mrido1

Wiki Fusion

1.5.5

stable

Andre Louis

Win Wizard

5.0.8

stable

Jakub Lukowicz

Window State

1.2.0

stable

Lanie

Windows App Essentials

26.09

stable

josephsl

Windows Magnifier

4.4

stable

Cyrille Bougot

WindowsOfProcess

2026.4.30

stable

沉浮 <394434124@qq.com>

WinForms .NET 4.8 Fixes

0.2.1

stable

Cary-rowen <manchen_0528@outlook.com>

WinForms Designer Accessibilizer

1.1.0

stable

Karl-Otto Rosenqvist

WinTeleport

0.3.3

stable

Cary-rowen <manchen_0528@outlook.com>

With Sounds

0.1.2

stable

zh-yx <zhyx-work@outlook.com>, Cary-rowen <cary-rowen@outlook.com>

Word Language Switching

1.5.1

stable

Barbara Henn - MBZ Ilvesheim

Word Predictor

1.7.1

stable

Lanie

WordBridge

2026.8.1

stable

Coseeing Community Contributors, Woody Tseng

WordNav

2.2.15

stable

Tony Malykh <anton.malykh@gmail.com>

WorldVoice

6.2

stable

Woody Tseng

xBlock

2026.5.1

stable

Chai Chaimee

Xinyi OCR

3.2.1

stable

huaiyinfeilong <huaiyinfeilong@163.com>

xPand

2026.5.1

stable

Chai Chaimee

xPlorer

2026.8.6

stable

Chai Chaimee

xTrack

2026.9.1

stable

Chai Chaimee

Yandex translator for NVDA

2026.05.08

stable

alekssamos

YouTube Access Pro

2026.08.20

stable

Peem Narkkhwan

Youtube Canlı Yayın Sohbet İstemcisi

1.7

stable

ADEM ERDOĞAN

YouTube Caption Reader

1.0.2

stable

Im Seongho

YouTubePlus

2026.8.21

stable

NVDA_TH

YTVideoDownloader

1.0

stable

Vatsal Gautam

Zoom Enhancements

26.09

stable

josephsl

### Custom braille tables and speech symbol dictionaries

IMPORTANT: this section covers modules that are not primarily written in Python and requires some knowledge of NVDA and/or its dependencies.

So far, we met modules primarily written in Python, including global plugins, app modules, drivers, and enhancers. This chapter covers more advanced module types where they require knowledge of NVDA internals and/or its dependencies. These modules are not primarily written in Python and are meant for specialized uses.

In addition to Python modules (see above), add-ons can include custom braille tables and speech symbol dictionaries, collectively known as processors and presenters. A custom braille table adds additional braille output and input tables, and a speech symbol dictionary enhances speech processing by adding additional pronunciation rules. These modules are useful in situations where reading and writing uncommon languages and symbols using speech and/or braille are useful such as studying ancient languages.

Developing these module types requires:

- Custom braille table: familiarity with Liblouis braille translator and its braille table format
- Speech symbol dictionary: NVDA's speech dictionary file format
Note: custom braille tables were introduced in NVDA 2024.3, and speech symbol dictionaries can be included starting with NVDA 2024.4.

### Introduction

Welcome to the NVDA Add-on Development Guide. This is the one-stop guide on how to develop NVDA add-ons. This guide also explains some useful code segments from the NVDA core source code, which highlight concepts for you, as you learn to write add-ons.

For more information on NVDA development, please visit the [NVDA GitHub page](https://github.com/nvaccess/nvda). Be sure to go over the [NVDA Developer Guide](https://www.nvaccess.org/files/nvda/documentation/developerGuide.html) to familiarize yourself with key terms and basics on getting started with add-on development.

### The message dialog API

The message dialog API provides a flexible way of presenting interactive messages to the user. The messages are highly customisable, with options to change icons and sounds, button labels, return values, and close behaviour, as well as to attach your own callbacks.

All classes that make up the message dialog API are importable from `gui.message`. While you are unlikely to need all of them, they are enumerated below:

- `ReturnCode`: Possible return codes from modal `MessageDialog`s.
- `EscapeCode`: Escape behaviour of `MessageDialog`s.
- `DialogType`: Types of dialogs (sets the dialog's sound and icon).
- `Button`: Button configuration data structure.
- `DefaultButton`: Enumeration of pre-configured buttons.
- `DefaultButtonSet`: Enumeration of common combinations of buttons.
- `MessageDialog`: The actual dialog class.
In many simple cases, you will be able to achieve what you need by simply creating a message dialog and calling `Show` or `ShowModal`. For example:

    from gui.message import MessageDialog
    from gui import mainFrame

    MessageDialog(
    	mainFrame,
    	_("Hello world!"),
    ).Show()

This will show a non-modal (that is, non-blocking) dialog with the text "Hello world!" and an OK button.

If you want the dialog to be modal (that is, to block the user from performing other actions in NVDA until they have responded to it), you can call `ShowModal` instead.

With modal dialogs, the easiest way to respond to user input is via the return code.

    from gui.message import DefaultButtonSet, ReturnCode

    saveDialog = MessageDialog(
    	mainFrame,
    	_("Would you like to save your changes before exiting?"),
    	_("Save changes?"),
    	buttons=DefaultButtonSet.SAVE_NO_CANCEL
    )

    match saveDialog.ShowModal():
    	case ReturnCode.SAVE:
    		...  # Save the changes and close
    	case ReturnCode.NO:
    		...  # Discard changes and close
    	case ReturnCode.CANCEL:
    		...  # Do not close

For non-modal dialogs, the easiest way to respond to the user pressing a button is via callback methods.

    from gui.message import Payload

    def readChangelog(payload: Payload):
    	...  # Do something

    def downloadUpdate(payload: Payload):
    	...  # Do something

    def remindLater(payload: Payload):
    	...  # Do something

    updateDialog = MessageDialog(
    	mainFrame,
    	"An update is available. "
    	"Would you like to download it now?",
    	"Update",
    	buttons=None,
    ).addYesButton(
    	callback=downloadUpdate
    ).addNoButton(
    	label=_("&Remind me later"),
    	fallbackAction=True,
    	callback=remindLater
    ).addHelpButton(
    	label=_("What's &new"),
    	callback=readChangelog
    )

    updateDialog.Show()

You can set many of the parameters to `addButton` later, too:

- The default focus can be set by calling `setDefaultFocus` on your message dialog instance, and passing it the ID of the button to make the default focus.
- The fallback action can be set later by calling `setFallbackAction` or `SetEscapeId` with the ID of the button which performs the fallback action.
- The button's label can be changed by calling `setButtonLabel` with the ID of the button and the new label.

#### Fallback actions

The fallback action is the action performed when the dialog is closed without the user pressing one of the buttons you added to the dialog. This can happen for several reasons:

- The user pressed `esc` or `alt+f4` to close the dialog.
- The user used the title bar close button or system menu close item to close the dialog.
- The user closed the dialog from the Task View, Taskbar or App Switcher.
- The user is quitting NVDA.
- Some other part of NVDA or an add-on has asked the dialog to close.
By default, the fallback action is set to `EscapeCode.CANCEL_OR_AFFIRMATIVE`. This means that the fallback action will be the cancel button if there is one, the button whose ID is `dialog.GetAffirmativeId()` (`ReturnCode.OK`, by default), or `None` if no button with either ID exists in the dialog. You can use `dialog.SetAffirmativeId(id)` to change the ID of the button used secondarily to Cancel, if you like. The fallback action can also be set to `EscapeCode.NO_FALLBACK` to disable closing the dialog like this entirely. If it is set to any other value, the value must be the id of a button to use as the default action.

In some cases, the dialog may be forced to close. If the dialog is shown modally, a calculated fallback action will be used if the fallback action is `EscapeCode.NO_FALLBACK` or not found. The order of precedence for calculating the fallback when a dialog is forced to close is as follows:

- The developer-set fallback action.
- The developer-set default focus.
- The first button added to the dialog that closes the dialog.
- The first button added to the dialog, regardless of whether it closes the dialog.
- A dummy action that does nothing but close the dialog. In this case, and only this case, the return code from showing the dialog modally will be `EscapeCode.NO_FALLBACK`.

#### A note on threading

IMPORTANT: Most `MessageDialog` methods are not thread safe. Calling these methods from non-GUI threads can cause crashes or unpredictable behavior.

When calling non thread safe methods on `MessageDialog` or its instances, be sure to do so on the GUI thread. To do this with wxPython, you can use `wx.CallAfter` or `wx.CallLater`. As these operations schedule the passed callable to occur on the GUI thread, they will return immediately, and will not return the return value of the passed callable. If you want to wait until the callable has completed, or care about its return value, consider using `gui.guiHelper.wxCallOnMain`.

The `wxCallOnMain` function executes the callable you pass to it, along with any positional and keyword arguments, on the GUI thread. It blocks the calling thread until the passed callable returns or raises an exception, at which point it returns the returned value, or re-raises the raised exception.

    # To call
    someFunction(arg1, arg2, kw1=value1, kw2=value2)
    # on the GUI thread:
    wxCallOnMain(someFunction, arg1, arg2, kw=value1, kw2=value2)

In fact, you cannot create, initialise, or show (modally or non-modally) `MessageDialog`s from any thread other than the GUI thread.

#### Buttons

You can add buttons in a number of ways:

- By passing a `Collection` of `Button`s to the `buttons` keyword-only parameter to `MessageDialog` when initialising.
- By calling `addButton` on a `MessageDialog` instance, either with a `Button` instance, or with simple parameters.
    - When calling `addButton` with a `Button` instance, you can override all of its parameters except `id` by providing their values as keyword arguments.
    - When calling `addButton` with simple parameters, the parameters it accepts are the same as those of `Button`.
    - In both cases, `id` or `button` is the first argument, and is positional only.
- By calling `addButtons` with a `Collection` of `Button`s.
- By calling any of the add button helpers.
Regardless of how you add them, you cannot add multiple buttons with the same ID to the same `MessageDialog`.

A `Button` is an immutable data structure containing all of the information needed to add a button to a `MessageDialog`. Its fields are as follows:

Field

Type

Default

Explanation

`id`

`ReturnCode`

No default

The ID used to refer to the button.

`label`

`str`

No default

The text label to display on the button. Prefix accelerator keys with an ampersand (&).

`callback`

`Callable` or `None`

`None`

The function to call when the button is clicked. This is most useful for non-modal dialogs.

`defaultFocus`

`bool`

`False`

Whether to explicitly set the button as the default focus. (1)

`fallbackAction`

`bool`

`False`

Whether the button should be the fallback action, which is called when the user presses `esc`, uses the system menu or title bar close buttons, or the dialog is asked to close programmatically. (2)

`closesDialog`

`bool`

`True`

Whether the button should close the dialog when pressed. (3)

`returnCode`

`ReturnCode` or `None`

`None`

Value to return when a modal dialog is closed. If `None`, the button's ID will be used.

- Setting `defaultFocus` only overrides the default focus:
    - If no buttons have this property, the first button will be the default focus.
    - If multiple buttons have this property, the last one will be the default focus.
- `fallbackAction` only sets whether to override the fallback action:
    - This button will still be the fallback action if the dialog's fallback action is set to `EscapeCode.CANCEL_OR_AFFIRMATIVE` (the default) and its ID is `ReturnCode.CANCEL` (or whatever the value of `GetAffirmativeId()` is (`ReturnCode.OK`, by default), if there is no button with `id=ReturnCode.CANCEL`), even if it is added with `fallbackAction=False`. To set a dialog to have no fallback action, use `setFallbackAction(EscapeCode.NO_FALLBACK)`.
    - If multiple buttons have this property, the last one will be the fallback action.
- Buttons with `fallbackAction=True` and `closesDialog=False` are not supported:
    - When adding a button with `fallbackAction=True` and `closesDialog=False`, `closesDialog` will be set to `True`.
    - If you attempt to call `setFallbackAction` with the ID of a button that does not close the dialog, `ValueError` will be raised.
A number of pre-configured buttons are available for you to use from the `DefaultButton` enumeration, complete with pre-translated labels. None of these buttons will explicitly set themselves as the fallback action. You can also add any of these buttons to an existing `MessageDialog` instance with its add button helper, which also allows you to override all but the `id` parameter. The following default buttons are available:

Button

Label

ID/return code

Closes dialog

Add button helper

`APPLY`

&Apply

`ReturnCode.APPLY`

No

`addApplyButton`

`CANCEL`

Cancel

`ReturnCode.CANCEL`

Yes

`addCancelButton`

`CLOSE`

Close

`ReturnCode.CLOSE`

Yes

`addCloseButton`

`HELP`

Help

`ReturnCode.HELP`

No

`addHelpButton`

`NO`

&No

`ReturnCode.NO`

Yes

`addNoButton`

`OK`

OK

`ReturnCode.OK`

Yes

`addOkButton`

`SAVE`

&Save

`ReturnCode.SAVE`

Yes

`addSaveButton`

`YES`

&Yes

`ReturnCode.YES`

Yes

`addYesButton`

As you usually want more than one button on a dialog, there are also a number of pre-defined sets of buttons available as members of the `DefaultButtonSet` enumeration. All of them comprise members of `DefaultButton`. You can also add any of these default button sets to an existing `MessageDialog` with one of its add buttons helpers. The following default button sets are available:

Button set

Contains

Add button set helper

Notes

`OK_CANCEL`

`DefaultButton.OK` and `DefaultButton.Cancel`

`addOkCancelButtons`

`YES_NO`

`DefaultButton.YES` and `DefaultButton.NO`

`addYesNoButtons`

You must set a fallback action if you want the user to be able to press escape to close a dialog with only these buttons.

`YES_NO_CANCEL`

`DefaultButton.YES`, `DefaultButton.NO` and `DefaultButton.CANCEL`

`addYesNoCancelButtons`

`SAVE_NO_CANCEL`

`DefaultButton.SAVE`, `DefaultButton.NO`, `DefaultButton.CANCEL`

`addSaveNoCancelButtons`

The label of the no button is overridden to be "Do&n't save".

If none of the standard `ReturnCode` values are suitable for your button, you may also use `ReturnCode.CUSTOM_1` through `ReturnCode.CUSTOM_5`, which will not conflict with any built-in identifiers.

#### Callbacks

A convenient way of responding to button presses, especially for non-modal message dialogs, is to attach callbacks to the buttons. This is achieved by passing a `callback` function to `addButton`, `addButtons`, or any of the add button helpers.

A callback should be a function which accepts exactly one positional argument. When called, a `Payload` data structure will be passed in. This data structure currently contains no information, though in future it may be augmented to contain information about the dialog's state and the context from which the callback was called.

#### Convenience methods

The `MessageDialog` class also provides a number of convenience methods for showing common types of modal dialogs. Each of them requires a message string, and optionally a title string and parent window. They all also support overriding the labels on their buttons via keyword arguments. They are all thread safe. The following convenience class methods are provided (keyword arguments for overriding button labels indicated in parentheses):

Method

Buttons

Return values

`alert`

OK (`okLabel`)

`None`

`confirm`

OK (`okLabel`) and Cancel (`cancelLabel`)

`ReturnCode.OK` or `ReturnCode.CANCEL`

`ask`

Yes (`yesLabel`), No (`noLabel`) and Cancel (`cancelLabel`)

`ReturnCode.YES`, `ReturnCode.NO` or `ReturnCode.CANCEL`
