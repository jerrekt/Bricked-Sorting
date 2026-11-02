// Bin receiver for Bricked Sorting (Indicate stage).
// The laptop bridge (indicate/bridge/bin_bridge.py) sends one line per piece, like "1-3".
// Move the chute to that bin, then answer "OK 1-3". Answer "ERR <reason>" if you can't.
// Also understands: "PING" -> "PONG", "HOME" -> home the axes, answers "OK HOME".
//
// Floor 1 = bottom row (bricks), floor 2 = top row. Slot 1-8 left to right; 8 = unknown color.
// Fill in moveTo() and homeAxes() with your motor code. Serial Monitor at 115200 to test by hand.

const long BAUD = 115200;
String line;

void homeAxes() {
  // TODO: drive Z and the turn axis to their limit switches.
}

bool moveTo(int floorNum, int slot) {
  // TODO: set height from floorNum and angle from slot, wait until the chute is there.
  // Return false if something goes wrong (limit hit, timeout) so the bridge gets ERR.
  Serial.print("moving to floor "); Serial.print(floorNum);
  Serial.print(" slot "); Serial.println(slot);   // extra prints are fine, the bridge shows them
  delay(300);                                     // stand-in for real motion
  return true;
}

void handle(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;
  if (cmd == "PING") { Serial.println("PONG"); return; }
  if (cmd == "HOME") { homeAxes(); Serial.println("OK HOME"); return; }
  // Expect exactly "F-S": F is 1 or 2, S is 1..8
  if (cmd.length() != 3 || cmd.charAt(1) != '-') { Serial.println("ERR bad command " + cmd); return; }
  int f = cmd.charAt(0) - '0', s = cmd.charAt(2) - '0';
  if (f < 1 || f > 2 || s < 1 || s > 8) { Serial.println("ERR out of range " + cmd); return; }
  if (moveTo(f, s)) Serial.println("OK " + cmd);
  else Serial.println("ERR move failed " + cmd);
}

void setup() {
  Serial.begin(BAUD);
  homeAxes();
  Serial.println("READY");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') { handle(line); line = ""; }
    else if (c != '\r' && line.length() < 32) line += c;
  }
}
