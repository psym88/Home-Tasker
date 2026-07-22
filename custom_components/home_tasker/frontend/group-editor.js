import { t } from "./localize.js";

export const withGroupEditor = Base => class extends Base {
  groupEditor(group=null){ const g=group||{}; this.dialog(t(group?"group.edit":"group.new"),[
    ["name",t("group.name"),g.name,true],["manufacturer",t("group.manufacturer"),g.manufacturer],["model",t("group.model"),g.model],["description",t("group.description"),g.description,false,"textarea"]
  ],async v=>{const payload={name:v.name,manufacturer:v.manufacturer||null,model:v.model||null,description:v.description||null};await this.ws({type:`home_tasker/group/${group?"update":"create"}`,...(group?{group_id:group.id}:{}),...payload});}); }
};
