// Tree-shaken Motion: only what static/js/app.js uses (animate with springs and number tweens).
import { animate } from "motion";
window.Motion = { animate };
