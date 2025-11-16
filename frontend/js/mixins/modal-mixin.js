// frontend/js/mixins/modal-mixin.js
const modalMixin = {
    data() {
        return {
            overlayClicked: false
        };
    },
    methods: {
        handleOverlayClick() {
            this.overlayClicked = true;
        },
        handleOverlayRelease() {
            if (this.overlayClicked) {
                this.$emit('close');
            }
            this.overlayClicked = false;
        }
    }
};