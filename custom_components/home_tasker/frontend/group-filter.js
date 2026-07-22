import { t } from "./localize.js";

export const GROUP_FILTER_TAG="home-tasker-group-filter";

export class HomeTaskerGroupFilter extends HTMLElement {
  constructor(){super();this.attachShadow({mode:"open"});this._groups=[];this._value=[];this.expanded=false;}
  set groups(value){this._groups=Array.isArray(value)?value:[];this.render();}
  get groups(){return this._groups;}
  set value(value){this._value=Array.isArray(value)?value:[];this.render();}
  get value(){return this._value;}
  connectedCallback(){this.render();}
  select(id){this._value=id?(this._value.includes(id)?this._value.filter(value=>value!==id):[...this._value,id]):[];this.dispatchEvent(new CustomEvent("value-changed",{bubbles:true,composed:true,detail:{value:this._value}}));this.render();}
  actionMenu(group){
    const dropdown=document.createElement("ha-dropdown"),button=document.createElement("ha-icon-button"),icon=document.createElement("ha-icon"),edit=document.createElement("ha-dropdown-item"),remove=document.createElement("ha-dropdown-item"),stop=event=>event.stopPropagation();
    dropdown.slot="meta";button.slot="trigger";button.label=t("group.actions");button.setAttribute("aria-label",t("group.actions"));icon.setAttribute("icon","mdi:dots-vertical");button.append(icon);
    edit.value="edit";edit.innerHTML=`<ha-icon slot="icon" icon="mdi:pencil"></ha-icon>${t("menu.edit")}`;
    remove.value="delete";remove.setAttribute("variant","danger");remove.innerHTML=`<ha-icon slot="icon" icon="mdi:delete"></ha-icon>${t("menu.delete")}`;
    dropdown.addEventListener("pointerdown",stop);dropdown.addEventListener("click",stop);dropdown.addEventListener("wa-select",async event=>{event.stopPropagation();const action=event.detail?.item?.value;if(action==="edit")this.controller?.groupEditor(group);if(action==="delete"&&await this.controller?.deleteGroup(group)&&this._value.includes(group.name))this.select(group.name);});
    dropdown.append(button,edit,remove);return dropdown;
  }
  render(){
    if(!this.shadowRoot)return;
    this.shadowRoot.innerHTML=`<style>:host{display:block;border-bottom:1px solid var(--divider-color)}ha-expansion-panel{--ha-card-border-radius:var(--ha-border-radius-square);--expansion-panel-content-padding:0}.header{display:flex;align-items:center}.badge{display:inline-block;box-sizing:border-box;min-width:16px;margin-inline-start:8px;padding:0 2px;border-radius:var(--ha-border-radius-circle);background:var(--primary-color);color:var(--text-primary-color);font-size:var(--ha-font-size-xs);font-weight:var(--ha-font-weight-normal);line-height:var(--ha-line-height-normal);text-align:center}ha-list{--mdc-list-item-meta-size:auto;--mdc-list-side-padding-right:var(--ha-space-1);--mdc-list-side-padding-left:var(--ha-space-4);--ha-icon-button-size:36px}ha-list-item{--mdc-list-item-graphic-margin:var(--ha-space-4)}ha-dropdown-item{font-size:var(--ha-font-size-m)}</style><ha-expansion-panel left-chevron><div slot="header" class="header">${t("task.group")}${this._value.length?`<span class="badge">${this._value.length}</span>`:""}</div><ha-list activatable></ha-list></ha-expansion-panel>`;
    const panel=this.shadowRoot.querySelector("ha-expansion-panel"),list=this.shadowRoot.querySelector("ha-list");panel.expanded=this.expanded;panel.addEventListener("expanded-changed",event=>{this.expanded=Boolean(event.detail?.expanded);});
    const all=document.createElement("ha-list-item");all.textContent=t("filter.show_all");all.selected=!this._value.length;all.activated=!this._value.length;all.addEventListener("click",()=>this.select(null));list.append(all);
    for(const group of this._groups){const item=document.createElement("ha-list-item"),icon=document.createElement("ha-icon");item.value=group.name;item.selected=this._value.includes(group.name);item.activated=item.selected;item.graphic="icon";item.hasMeta=true;icon.slot="graphic";icon.setAttribute("icon","mdi:devices");item.append(icon,document.createTextNode(group.name),this.actionMenu(group));item.addEventListener("click",()=>this.select(group.name));list.append(item);}
  }
}

if(!customElements.get(GROUP_FILTER_TAG))customElements.define(GROUP_FILTER_TAG,HomeTaskerGroupFilter);
