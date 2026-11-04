# Aggregates physical input state into desired keyboard/gamepad output and
# applies only the deltas. Hardware-independent: the keyboard and gamepad
# objects are supplied by the caller, so this module never touches board or
# USB modules itself.
#
# Action dicts come from ProfileHelper.getAction():
# {"type": 1, "action": keycode}  -> keyboard key (modifiers detected by keycode)
# {"type": 2, "action": 1-16}     -> gamepad button
# {"type": 3, "action": "nextProfile"/"previousProfile"} -> profile navigation
# {"type": 4, "action": "hat"}    -> hat (POV) direction source
# {"type": None, ...} or None     -> disabled/unknown binding

_MODIFIER_FIRST_KEYCODE = 0xE0
_MODIFIER_LAST_KEYCODE = 0xE7
_MAX_REGULAR_KEYS = 6


def _isProfileNavigation(binding):
    # A profile-next/previous binding. Held controls with one of these on
    # either side of a transition are latched so they cannot repeat the
    # navigation or activate an unrelated binding in the new profile.
    return (
        binding is not None
        and binding["type"] == 3
        and (binding["action"] == "nextProfile" or binding["action"] == "previousProfile")
    )

class ActionManager:
    def __init__(self, keyboard, gamepad):
        self.keyboard = keyboard
        self.gamepad = gamepad
        # stateName -> action dict or None
        self._bindings = {}
        # stateName -> physical pressed state (tracked even with no/None binding)
        self._physical = {}
        # (stateName, direction) pairs for controls that can feed the hat
        self._hatDirections = []
        # Controls latched by a profile transition; they produce no keyboard,
        # gamepad, hat, or profile output until physically released.
        self._latchedControls = set()
        # Pending profile navigation edges and the control that edged them
        self._navNext = False
        self._navPrevious = False
        self._navNextOrigin = None
        self._navPreviousOrigin = None
        # Successfully applied HID output, used to calculate deltas
        self._appliedKeys = []
        self._appliedModifierMask = 0
        self._appliedButtonMask = 0
        self._appliedHat = 0
        # Reused scratch buffer; no new list is created per recompute
        self._desiredKeys = []
        # Snapshot of bindings taken by beginProfileTransition so the latch
        # rules can compare old and new bindings after the new set is installed
        self._oldBindings = {}
        self._dirty = False

    def registerControl(self, name, hatDirection=None):
        if name in self._bindings:
            return

        self._bindings[name] = None
        self._physical[name] = False

        if hatDirection is not None:
            self._hatDirections.append((name, hatDirection))

    def setBinding(self, name, action):
        self.registerControl(name)
        self._bindings[name] = action
        self._dirty = True

    def setPhysicalState(self, name, pressed):
        self.registerControl(name)
        pressed = bool(pressed)

        if self._physical[name] == pressed:
            return

        self._physical[name] = pressed

        if not pressed:
            self._latchedControls.discard(name)

        if pressed and name not in self._latchedControls:
            binding = self._bindings[name]

            if binding is not None and binding["type"] == 3:
                # Profile navigation fires only on a fresh pressed edge,
                # never from output reconciliation.
                if binding["action"] == "nextProfile":
                    self._navNext = True
                    self._navNextOrigin = name
                elif binding["action"] == "previousProfile":
                    self._navPrevious = True
                    self._navPreviousOrigin = name

        self._dirty = True

    def getPhysicalState(self, name):
        return self._physical.get(name, False)

    def consumeNavigation(self):
        # Mirrors the old code.py semantics: when both directions were edged
        # in one iteration, next wins and the pending previous is dropped.
        # Returns (action, originName), or (None, None) when nothing is
        # pending; originName is the control whose press edged the request.
        if self._navNext:
            action = "nextProfile"
            origin = self._navNextOrigin
            self._navNext = False
            self._navNextOrigin = None
            self._navPrevious = False
            self._navPreviousOrigin = None
            return (action, origin)

        if self._navPrevious:
            action = "previousProfile"
            origin = self._navPreviousOrigin
            self._navPrevious = False
            self._navPreviousOrigin = None
            return (action, origin)

        return (None, None)

    def _computeHat(self):
        up = False
        right = False
        down = False
        left = False

        for entry in self._hatDirections:
            name = entry[0]

            if name in self._latchedControls:
                continue

            binding = self._bindings[name]

            # Only directions whose current binding is the hat action count;
            # a direction bound to a key, button, profile action, or disabled
            # action must not leak into the hat report.
            if binding is None or binding["type"] != 4 or not self._physical[name]:
                continue

            direction = entry[1]

            if direction == "up":
                up = True
            elif direction == "right":
                right = True
            elif direction == "down":
                down = True
            elif direction == "left":
                left = True

        hatValue = 0

        if up and not down:
            hatValue = 1

            if right and not left:
                hatValue = 2
            elif left and not right:
                hatValue = 8
        elif down and not up:
            hatValue = 5

            if right and not left:
                hatValue = 4
            elif left and not right:
                hatValue = 6
        elif right and not left:
            hatValue = 3
        elif left and not right:
            hatValue = 7

        return hatValue

    def _recomputeDesired(self):
        desiredKeys = self._desiredKeys
        desiredKeys.clear()
        desiredModifierMask = 0
        desiredButtonMask = 0

        for name in self._bindings:
            if not self._physical[name] or name in self._latchedControls:
                continue

            binding = self._bindings[name]

            if binding is None:
                continue

            actionType = binding["type"]

            if actionType == 1:
                keycode = binding["action"]

                if _MODIFIER_FIRST_KEYCODE <= keycode <= _MODIFIER_LAST_KEYCODE:
                    # Modifiers are independent of the six-regular-key limit.
                    desiredModifierMask |= 1 << (keycode - _MODIFIER_FIRST_KEYCODE)
                elif keycode not in desiredKeys:
                    # Two controls holding the same key produce one entry.
                    desiredKeys.append(keycode)
            elif actionType == 2:
                desiredButtonMask |= 1 << (binding["action"] - 1)

        return (desiredModifierMask, desiredButtonMask, self._computeHat())

    def applyOutputs(self):
        # Recompute and flush only when physical state or bindings changed;
        # a no-change loop iteration does no work and allocates nothing.
        if not self._dirty:
            return

        self._dirty = False

        desiredModifierMask, desiredButtonMask, hatValue = self._recomputeDesired()
        desiredKeys = self._desiredKeys

        # Regular keys: release first so a freed slot can be reused by a new
        # press in this same flush. Still-applied keys are preserved even when
        # more than six are desired; the overflow simply stays pending.
        appliedKeys = self._appliedKeys
        index = len(appliedKeys) - 1

        while index >= 0:
            keycode = appliedKeys[index]

            if keycode not in desiredKeys:
                self.keyboard.release(keycode)
                appliedKeys.pop(index)

            index -= 1

        for keycode in desiredKeys:
            if len(appliedKeys) >= _MAX_REGULAR_KEYS:
                break

            if keycode not in appliedKeys:
                self.keyboard.press(keycode)
                appliedKeys.append(keycode)

        changedModifiers = self._appliedModifierMask ^ desiredModifierMask
        self._appliedModifierMask = desiredModifierMask

        for bit in range(8):
            mask = 1 << bit

            if changedModifiers & mask:
                if desiredModifierMask & mask:
                    self.keyboard.press(_MODIFIER_FIRST_KEYCODE + bit)
                else:
                    self.keyboard.release(_MODIFIER_FIRST_KEYCODE + bit)

        changedButtons = self._appliedButtonMask ^ desiredButtonMask
        self._appliedButtonMask = desiredButtonMask

        if changedButtons:
            mask = 1
            button = 1

            while changedButtons:
                if changedButtons & mask:
                    if desiredButtonMask & mask:
                        self.gamepad.press_buttons(button)
                    else:
                        self.gamepad.release_buttons(button)

                    changedButtons &= ~mask

                mask <<= 1
                button += 1

        if hatValue != self._appliedHat:
            self.gamepad.set_hat(hatValue)
            self._appliedHat = hatValue

    def beginProfileTransition(self):
        # Snapshot the current bindings. The caller installs the new profile's
        # bindings next and then calls applyProfileTransition(); the snapshot
        # lets the latch rules see both the old and the new binding of every
        # held control even though the bindings were replaced in place.
        oldBindings = self._oldBindings
        oldBindings.clear()

        for name in self._bindings:
            oldBindings[name] = self._bindings[name]

    def applyProfileTransition(self, originName=None):
        # Immediate layer-style remap, shared by navigation and serial active-
        # profile selection. Held ordinary controls activate their new
        # bindings right away; applyOutputs diffs the old and new desired
        # output, so an output that is equivalent in both profiles stays
        # pressed instead of getting a release/repress pair.
        physical = self._physical
        latch = self._latchedControls

        # A latch always ends on physical release; drop any stale entries.
        released = []

        for name in latch:
            if not physical.get(name, False):
                released.append(name)

        for name in released:
            latch.discard(name)

        # Latch the control that initiated the change, plus every other held
        # control whose old or new binding is profile navigation. A latched
        # control produces no keyboard, gamepad, hat, or further profile
        # action until it is released, so the layer switch control cannot
        # repeat or activate an unrelated binding in the new profile.
        for name in physical:
            if not physical[name]:
                continue

            if name == originName:
                latch.add(name)
            elif name not in latch and (
                _isProfileNavigation(self._oldBindings.get(name))
                or _isProfileNavigation(self._bindings[name])
            ):
                latch.add(name)

        self._navNext = False
        self._navPrevious = False
        self._navNextOrigin = None
        self._navPreviousOrigin = None
        self._dirty = True
        self.applyOutputs()
