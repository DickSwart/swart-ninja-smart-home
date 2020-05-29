import {
  LitElement, html
} from 'https://unpkg.com/@polymer/lit-element@^0.5.2/lit-element.js?module';

class InvisibleCard extends LitElement  {
  static get properties() {
    return {
      hass: Object,
      config: Object,
    }
  }

  _render({ hass, config }) {
    return html``;
  }

  setConfig(config) {
    this.config = config;
  }

  getCardSize() {
    return 0;
  }
}

customElements.define('invisible-card', InvisibleCard);