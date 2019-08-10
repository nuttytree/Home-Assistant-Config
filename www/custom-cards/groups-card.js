class GroupsCard extends HTMLElement {

  setConfig(config) {
    if (!config.groups) {
      throw new Error('Please specify some groups');
    }
    if (!config.entities) {
      config.entities = [];
    }
    if (!config.exclude) {
      config.exclude = [];
    }

    if (this.lastChild) this.removeChild(this.lastChild);
    const cardConfig = Object.assign({}, config);
    if (!cardConfig.card) cardConfig.card = {};
    if (!cardConfig.card.type) cardConfig.card.type = 'entities';
    const element = document.createElement(`hui-${cardConfig.card.type}-card`);
    this.appendChild(element);
    this._config = cardConfig;
  }

  set hass(hass) {
    const config = this._config;
    var entities = [];
    entities.push(...config.entities.filter(e => hass.states[e].attributes['hidden'] != true));
    config.groups.forEach(function(group) {
      var groupEntities = hass.states[group].attributes['entity_id'];
      entities.push(...groupEntities.filter(e => hass.states[e].attributes['hidden'] != true && !config.exclude.includes(e)))
    });
    if (!config.card.entities || config.card.entities.length !== entities.length ||
      !config.card.entities.every((value, index) => value.entity === entities[index].entity)) {
      config.card.entities = entities;
    }
    this.lastChild.setConfig(config.card);
    this.lastChild.hass = hass;
  }

  getCardSize() {
    return 'getCardSize' in this.lastChild ? this.lastChild.getCardSize() : 1;
  }
}

customElements.define('groups-card', GroupsCard);