
odoo.define('pao_discuss_channels_access.custom_feature', function (require) {
    "use strict";
    const { Component } = require("@odoo/owl");
  
    class MyChannelSelector extends Component {
      // Override the fetchSuggestions function or other methods as needed
        async fetchSuggestions() {
        const cleanedTerm = cleanTerm(this.state.value);
        if (cleanedTerm) {
            if (this.props.category.id === "channels") {
                const domain = [
                    ["channel_type", "=", "channel"],
                    ["name", "ilike", cleanedTerm],
                ];
                const fields = ["name"];
                const results = await this.sequential(async () => {
                    this.state.navigableListProps.isLoading = true;
                    
                    const res = await this.orm.searchRead("discuss.channel", domain, fields, {
                        limit: 10, context: { sudo: true },
                    });
                    this.state.navigableListProps.isLoading = false;
                    return res;
                });
                if (!results) {
                    this.state.navigableListProps.options = [];
                    return;
                }
                const choices = results.map((channel) => {
                    return {
                        channelId: channel.id,
                        classList: "o-discuss-ChannelSelector-suggestion",
                        label: channel.name,
                    };
                });
                choices.push({
                    channelId: "__create__",
                    classList: "o-discuss-ChannelSelector-suggestion",
                    label: cleanedTerm,
                });
                this.state.navigableListProps.options = choices;
                return;
            }
            if (this.props.category.id === "chats") {
                const results = await this.sequential(async () => {
                    this.state.navigableListProps.isLoading = true;
                    const res = await this.orm.call("res.partner", "im_search", [
                        cleanedTerm,
                        10,
                        this.state.selectedPartners,
                    ]);
                    this.state.navigableListProps.isLoading = false;
                    return res;
                });
                if (!results) {
                    this.state.navigableListProps.options = [];
                    return;
                }
                const suggestions = this.suggestionService
                    .sortPartnerSuggestions(results, cleanedTerm)
                    .map((data) => {
                        this.store.Persona.insert({ ...data, type: "partner" });
                        return {
                            classList: "o-discuss-ChannelSelector-suggestion",
                            label: data.name,
                            partner: data,
                        };
                    });
                if (this.store.self.name.includes(cleanedTerm)) {
                    suggestions.push({
                        classList: "o-discuss-ChannelSelector-suggestion",
                        label: this.store.self.name,
                        partner: this.store.self,
                    });
                }
                if (suggestions.length === 0) {
                    suggestions.push({
                        classList: "o-discuss-ChannelSelector-suggestion",
                        label: _t("No results found"),
                        unselectable: true,
                    });
                }
                this.state.navigableListProps.options = suggestions;
                return;
            }
        }
        this.state.navigableListProps.options = [];
        return;
        }
    }
  
    // Register the custom component (optional)
    Component.register('MyChannelSelector', MyChannelSelector);
  
    return MyChannelSelector;
  });
  
