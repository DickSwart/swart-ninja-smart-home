// name: Random RGBA Light Color Object
// outputs: 1
// outputs: 1
// https://github.com/davidmerfield/randomColor
var randomColor = global.get('randomColor');// import the script
var color = randomColor({
   format: 'rgba' // e.g. 'rgb(225,200,20)'
}); // a hex code for an attractive color

var match = color.match(/rgba?\((\d{1,3}), ?(\d{1,3}), ?(\d{1,3})\)?(?:, ?(\d(?:\.\d+?))\))?/);

var colorObject = match ? {
  "brightness": Math.round(Number(match[4])*255),
  "rgb_color": [Number(match[1]),Number(match[2]),Number(match[3])]
} : {};
  
node.warn(color);
msg.payload = colorObject;
return msg;