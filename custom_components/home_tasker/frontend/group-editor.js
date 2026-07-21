export const withGroupEditor = Base => class extends Base {
  groupEditor(group=null){ const g=group||{}; this.dialog(group?"Gruppe bearbeiten":"Neue Gruppe",[
    ["name","Name",g.name,true],["manufacturer","Hersteller",g.manufacturer],["model","Modell",g.model],["description","Beschreibung",g.description,false,"textarea"]
  ],async v=>{const payload={name:v.name,manufacturer:v.manufacturer||null,model:v.model||null,description:v.description||null};await this.ws({type:`home_tasker/group/${group?"update":"create"}`,...(group?{group_id:group.id}:{}),...payload});await this.load();}); }
};
