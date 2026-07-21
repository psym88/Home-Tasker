import { showTaskDialog } from "./native-task-dialog.js";

export const withTaskViewer = Base => class extends Base {
  taskViewer(task){showTaskDialog(this,task);}
};
