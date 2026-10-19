import AppKit
import CoreGraphics
import Vision

let args = CommandLine.arguments

func click(_ point: CGPoint) {
    CGWarpMouseCursorPosition(point)
    usleep(150_000)
    CGEvent(mouseEventSource: nil, mouseType: .leftMouseDown, mouseCursorPosition: point, mouseButton: .left)?.post(tap: .cghidEventTap)
    usleep(80_000)
    CGEvent(mouseEventSource: nil, mouseType: .leftMouseUp, mouseCursorPosition: point, mouseButton: .left)?.post(tap: .cghidEventTap)
}

if args.count >= 4 && args[1] == "--point" {
    guard let px = Double(args[2]), let py = Double(args[3]) else { exit(2) }
    click(CGPoint(x: px, y: py))
    exit(0)
}

guard args.count >= 7 else {
    FileHandle.standardError.write("usage: find_and_click <img> <target> <x> <y> <w> <h> [--dry]\n".data(using: .utf8)!)
    exit(2)
}
let imgPath = args[1]
let target = args[2]
let winX = Double(args[3])!
let winY = Double(args[4])!
let winW = Double(args[5])!
let winH = Double(args[6])!
let dryRun = args.contains("--dry")

guard let img = NSImage(contentsOfFile: imgPath),
      let tiff = img.tiffRepresentation,
      let rep = NSBitmapImageRep(data: tiff),
      let cg = rep.cgImage else {
    exit(2)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
request.recognitionLanguages = ["zh-Hans", "en-US"]
try VNImageRequestHandler(cgImage: cg, options: [:]).perform([request])

var best: (Double, Double)? = nil
for obs in request.results ?? [] {
    guard let candidate = obs.topCandidates(1).first else { continue }
    guard candidate.string.contains(target) else { continue }
    let box = obs.boundingBox
    let px = winX + box.midX * winW
    let py = winY + (1 - box.midY) * winH
    if py < winY + 60 { continue }
    if best == nil || py < best!.1 {
        best = (px, py)
    }
}

guard let (px, py) = best else { exit(1) }
print("\(px) \(py)")
if dryRun { exit(0) }

let point = CGPoint(x: px, y: py)
click(point)
