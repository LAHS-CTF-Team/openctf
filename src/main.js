// OpenCTF

// import bootstrap
import "bootstrap";

// Import styles
import style from "./main.scss";
// "use" the styles
((_s)=>{})(style);

// svelte
import App from "./App.html";

console.log(API_BASE);

const app = new App({
  target : document.body,
});
window.app = app;

export default app;
