In Quell, the game happens in a 2D grid.

## Ruleset
The following entities exist in the grid, or it can be empty.

1. Droplet (movable)
2. Wall (stationary)
3. Spike (stationary)
4. Pearl (stateful, can disappear)
5. Box (movable)
6. Portal (stationary)
7. Gate (stateful, can be open or close)
8. Button (stationary)
9. Rotatable Directional Spike (stationary)
...
and new entity may be introduced in later levels.

Spike has two subtypes:
- direction spike: only 1 side is spike, other 3 sides are wall and behave like wall.
- omin spike: all 4 sides are spike.

Additionally there's a global state button direction if button appears in the level.

Portal always come in pairs and each have a unique id.

Most entities occupy a space and are mutually exclusive, can only occupy 1 cell of the grid.

The game state changes by moving droplet. a play can make a drople attempt to move on 1 of the 4 direction. a then it follow this rule when encountering other entities, until infinite loop (failure), all pearls collected (success) or all movable object stops or destroys.:
- empty: droplet will keep moving in the same direction. note that if out of boundary, it would check the other side of the board (so up is connected to bottom and left is connected to right.)
- another droplet: the stationary droplet will disappear (because it merges with the other droplet), moving droplet keep moving in the same direction.
- wall: droplet would stop.
- Spike: droplet will be destroyed.
- Pearl: pearl will be collected and destroy, droplet keep moving. The game ends as successful the moment the last pearl is collected.
- Box: the box will attempt to move on the same direction along with the droplet. if the box cannot move, the droplet will also stop.
- Portal: the droplet will teleport to the other side of the portal maintaining the same direction.
- Gate (open): treat as empty. The gate will be activated and become closed as soon as the droplet leave the cell. Note that once activated the 
- Gate (close): Treat as wall.
- Button: treat as empty. however, upon entering this cell, a global state recording the direction will trigger. all Rotatable Directional Spike will point to the same direction (for example, if move from left to right, all directional spike will point to the right.)
- Rotatable Directional Spike: treat as Directional spike.

The box is also movable if pushed by a droplet(they move in the same step concurrently), and follow this rule:
- empty, wall, portal, gate, button: same as droplet
- droplet, spike (include rotatable directional spike), pearl: treat as wall and stop.
- another box: both box will disappear.

An infinite loop (failure) is defined if the exact same state is reached without any state change, the most common form is a droplet moving in one direction non-stop.


## Rendering
The board is rendered as light gray.
- The droplet is a cyan circle.
- The wall is a Dark Gray square.
- The spike is a small Red Square, on which an arrow is added for the direction of the spike, or a star if it is omini direction.
- Pearl is a small white cirtle.
- Box is a Brown square.
- Portal is a yellow ring.
- Gate if open is a tiny green circle. If closed, it is 9 tiny green circle evenly distributed on a square.
- Button is a small red arrow, all showing the global direction.
- Rotatable Direction Spike is the same as direction spike except using orange color for the square.

## Level editor

The level editor contains all the entity above as a side bar, and user can switch entity type by clicking on the icon. left click adds entity, right click removes it, R rotate the current entity in the cell.

The portal needs to have a way set its id.

There's also a feature to enlarge or reduce the grid width or height.

Hit S to save, and if it is a valid save, also quit. Save to questions/{level_id}.txt