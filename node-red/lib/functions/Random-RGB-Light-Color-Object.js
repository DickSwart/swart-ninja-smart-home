// name: Random RGB Light Color Object
// outputs: 1
// https://github.com/davidmerfield/randomColor
var randomColor = global.get('randomColor');// import the script
var color = randomColor({
   format: 'rgb' // e.g. 'rgb(225,200,20)'
});

var match = color.match(/rgba?\((\d{1,3}), ?(\d{1,3}), ?(\d{1,3})\)?(?:, ?(\d(?:\.\d+?))\))?/);

var colorObject = match ? {
  "rgb_color": [Number(match[1]),Number(match[2]),Number(match[3])]
} : {};
  
node.warn(color);
msg.payload = {
    data:colorObject
}
return msg;