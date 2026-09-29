// Deterministic, pauseable tour clock. No frame-rate or wall-clock dependence.
export const TOUR_ORDER=[0,5,3,4,1,2];
export const LEG_SECONDS=9,HOLD_SECONDS=9;
export class TourClock {
 constructor(){this.reset();}
 reset(){this.elapsed=0;this.running=false;this.finished=false;}
 start(){this.reset();this.running=true;}
 pause(){this.running=false;}
 resume(){if(!this.finished)this.running=true;}
 seek(stop){this.elapsed=Math.max(0,Math.min(5,stop))*(LEG_SECONDS+HOLD_SECONDS);this.finished=false;}
 tick(dt){if(this.running){this.elapsed+=Math.max(0,Math.min(dt,.1));if(this.elapsed>=TOUR_ORDER.length*(LEG_SECONDS+HOLD_SECONDS)){this.elapsed=TOUR_ORDER.length*(LEG_SECONDS+HOLD_SECONDS)-.001;this.finished=true;this.running=false;}}return this.state();}
 state(){const span=LEG_SECONDS+HOLD_SECONDS,step=Math.min(5,Math.floor(this.elapsed/span)),phase=this.elapsed-step*span;return {step,place:TOUR_ORDER[step],travel:Math.min(1,phase/LEG_SECONDS),progress:this.elapsed/(6*span),holding:phase>=LEG_SECONDS,finished:this.finished};}
}
