var autocomplete = autocomplete || (function () {
    const properties = [
        'direction',
        'boxSizing',
        'width',
        'height',
        'overflowX',
        'overflowY',

        'borderTopWidth',
        'borderRightWidth',
        'borderBottomWidth',
        'borderLeftWidth',
        'borderStyle',

        'paddingTop',
        'paddingRight',
        'paddingBottom',
        'paddingLeft',

        'fontStyle',
        'fontVariant',
        'fontWeight',
        'fontStretch',
        'fontSize',
        'fontSizeAdjust',
        'lineHeight',
        'fontFamily',

        'textAlign',
        'textTransform',
        'textIndent',
        'textDecoration',

        'letterSpacing',
        'wordSpacing',

        'tabSize',
        'MozTabSize',
    ]

    const isFirefox = typeof window !== 'undefined' && window['mozInnerScreenX'] != null;

    /**;
     * @param {HTMLTextAreaElement} element;
     * @param {number} position;
     */
    function getCaretCoordinates(element, position) {
        const div = document.createElement('div');
        document.body.appendChild(div);

        const style = div.style;
        const computed = getComputedStyle(element);

        style.whiteSpace = 'pre-wrap';
        style.wordWrap = 'break-word';
        style.position = 'absolute';
        style.visibility = 'hidden';

        properties.forEach(prop => {
            style[prop] = computed[prop];
        });

        if (isFirefox) {
            if (element.scrollHeight > parseInt(computed.height))
                style.overflowY = 'scroll';
        } else {
            style.overflow = 'hidden';
        }

        div.textContent = element.value.substring(0, position);

        const span = document.createElement('span');
        span.textContent = element.value.substring(position) || '.';
        div.appendChild(span);

        const coordinates = {
            top: span.offsetTop + parseInt(computed['borderTopWidth']),
            left: span.offsetLeft + parseInt(computed['borderLeftWidth']),
            // height: parseInt(computed['lineHeight']);
            height: span.offsetHeight,
        };

        div.remove();

        return coordinates;
    }

    class Mentionify {
        constructor(ref, menuRef, replaceFn, menuItemFn) {
            this.ref = ref;
            this.menuRef = menuRef;
            this.replaceFn = replaceFn;
            this.menuItemFn = menuItemFn;
            this.options = [];

            this.makeOptions = this.makeOptions.bind(this);
            this.closeMenu = this.closeMenu.bind(this);
            this.selectItem = this.selectItem.bind(this);
            this.onInput = this.onInput.bind(this);
            this.onKeyDown = this.onKeyDown.bind(this);
            this.renderMenu = this.renderMenu.bind(this);

            this.ref.addEventListener('input', this.onInput);
            this.ref.addEventListener('keydown', this.onKeyDown);
        };

        makeOptions(query) {
            const obj = this;
            fetch('/users-autocomplete/?q=' + query)
                .then(RES => RES.json())
                .then(function (res) {
                    const options = res['results'];
                    if (options.length !== 0) {
                        obj.options = options;
                        obj.renderMenu();
                    } else {
                        obj.closeMenu();
                    }
                });
        }

        closeMenu() {
            setTimeout(() => {
                this.options = [];
                this.left = undefined;
                this.top = undefined;
                this.triggerIdx = undefined;
                this.renderMenu();
            }, 0);
        }

        selectItem(active) {
            return () => {
                const preMention = this.ref.value.substring(0, this.triggerIdx);
                const option = this.options[active];
                const mention = this.replaceFn(option, this.ref.value[this.triggerIdx]);
                const postMention = this.ref.value.substring(this.ref.selectionStart);
                this.ref.value = `${preMention}${mention}${postMention}`;
                const caretPosition = this.ref.value.length - postMention.length;
                this.ref.setSelectionRange(caretPosition, caretPosition);
                this.closeMenu();
                this.ref.focus();
            };
        };

        onInput(ev) {
            const positionIndex = this.ref.selectionStart;
            const textBeforeCaret = this.ref.value.slice(0, positionIndex);
            const tokens = textBeforeCaret.split(/\s/);
            const lastToken = tokens[tokens.length - 1];
            const triggerIdx = textBeforeCaret.endsWith(lastToken)
                ? textBeforeCaret.length - lastToken.length
                : -1;
            const maybeTrigger = textBeforeCaret[triggerIdx];
            const keystrokeTriggered = maybeTrigger === '@';

            if (!keystrokeTriggered) {
                this.closeMenu();
                return;
            }

            const query = textBeforeCaret.slice(triggerIdx + 1);
            this.makeOptions(query);

            const coords = getCaretCoordinates(this.ref, positionIndex);
            const {top, left} = this.ref.getBoundingClientRect();

            setTimeout(() => {
                this.active = 0;
                this.left = window.scrollX + coords.left + left + this.ref.scrollLeft;
                this.top = window.scrollY + coords.top + top + coords.height - this.ref.scrollTop;
                this.triggerIdx = triggerIdx;
                this.renderMenu();
            }, 0);
        };

        onKeyDown(ev) {
            let keyCaught = false;
            if (this.triggerIdx !== undefined) {
                switch (ev.key) {
                    case 'ArrowDown':
                        this.active = Math.min(this.active + 1, this.options.length - 1);
                        this.renderMenu();
                        keyCaught = true;
                        break;
                    case 'ArrowUp':
                        this.active = Math.max(this.active - 1, 0);
                        this.renderMenu();
                        keyCaught = true;
                        break;
                    case 'Enter':
                    case 'Tab':
                        this.selectItem(this.active)();
                        keyCaught = true;
                        break;
                }
            }

            if (keyCaught) {
                ev.preventDefault();
            }
        };

        renderMenu() {
            if (this.top === undefined) {
                this.menuRef.hidden = true;
                return;
            }

            this.menuRef.style.left = this.left + 'px';
            this.menuRef.style.top = this.top + 'px';
            this.menuRef.innerHTML = '';

            this.options.forEach((option, idx) => {
                this.menuRef.appendChild(this.menuItemFn(
                    option,
                    this.selectItem(idx),
                    this.active === idx))
            });

            this.menuRef.hidden = false;
        };
    }

    const replaceFn = (user, trigger) => `${trigger}${user.username} `;

    const menuItemFn = (user, setItem, selected) => {
        const div = document.createElement('div');
        div.setAttribute('role', 'option');
        div.className = 'autocomplete-menu-item';
        if (selected) {
            div.classList.add('selected');
            div.setAttribute('aria-selected', '');
        }
        div.innerHTML = `<div style="display: flex;flex-direction: row;width: 150px;margin-bottom: 4px;">
            <div>
                <img src="/media${user.profile_pic}"
                     class="user-card-img-small"
                     onerror="this.onerror=null; this.src='/media/default_pics/no_pic.jpg'" 
                     alt="${user.name}">
            </div>
            <small class="p-1">
               ${user.name || user.username}
            </small>
        </div>`;
        div.onclick = setItem;
        return div;
    };
    return {
        init: Mentionify,
        replaceFn: replaceFn,
        menuItemFn: menuItemFn,
    };
})();