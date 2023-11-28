(function () {
    function tagTemplate(tagData) {
        return `
            <tag ${this.getAttributes(tagData)}
                    title="${tagData.username}"
                    contenteditable='false'
                    spellcheck='false'
                    tabIndex="-1"
                    class="tagify__tag ${tagData.class ? tagData.class : ""}" >
                <x title='' class='tagify__tag__removeBtn' role='button' aria-label='remove tag'></x>
                <div>
                    <div class='tagify__tag__avatar-wrap'>
                        <img onerror="this.style.visibility='hidden'" src="/media${tagData['profile_pic']}"/>
                    </div>
                    <span class='tagify__tag-text'>${tagData.name || tagData.username}</span>
                </div>
            </tag>
        `;
    }

    function suggestionItemTemplate(tagData) {
        return `
        <div ${this.getAttributes(tagData)}
            class='tagify__dropdown__item ${tagData.class ? tagData.class : ""}'
            tabindex="0"
            role="option"
            disabled=${tagData.disabled}>          
            <div class='tagify__dropdown__item__avatar-wrap'>
                <img onerror="this.style.visibility='hidden'" src="/media${tagData['profile_pic']}">
            </div>
            <div>
                <strong>${tagData.name || tagData.username}</strong>
                <span> (${tagData.username})</span>
            </div>
            <span>${tagData.email}${tagData['disabled'] ? ' - ' + tagData['disabled-message'] : ""}</span>
        </div>
    `
    }

    let tagsEl = document.getElementById('usersList');
    let tagify = new Tagify(tagsEl, {
            id: 'usersListTagify',
            tagTextProp: 'name',
            skipInvalid: true,
            enforceWhitelist: true,
            dropdown: {
                highlightFirst: true,
                classname: 'users-list',
                searchKeys: ['username', 'name', 'email']
            },
            duplicates: false,
            highlightFirst: true,
            templates: {
                tag: tagTemplate,
                dropdownItem: suggestionItemTemplate
            },
            originalInputValueFormat: valuesArr => valuesArr.map(item => item.value).join(','),
            autoComplete: {rightKey: true,},
        }),
        controller; // for aborting the call;
    tagify.on('input', onInput);

    function onInput(e) {
        tagify.whitelist = null;
        tagify.loading(true).dropdown.hide();
        let selectedUsernames = []
        for (const user of tagify.value) {
            selectedUsernames.push(user.username);
        }

        fetch('/users-autocomplete/?q=' + e.detail.value + '&selected=' + selectedUsernames)
            .then(res => res.json())
            .then(function (res) {
                tagify.settings.whitelist = res['results'].concat(tagify.value); // update inwhitelist Array in-place
                tagify.blacklist = [];
                tagify.loading(false).dropdown.show(e.detail.value); // render the suggestions dropdown
                for (const result of res['results']) {
                    if (result['disabled']) {
                        tagify.blacklist.push(result);
                    }
                }
            });
    }
})();
