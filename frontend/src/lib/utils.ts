import * as React from "react"

export function cn(...classes: (string | false | undefined)[]) {
  return React.Children.toArray(classes)
    .filter((c): c is string => typeof c === "string")
    .join(" ")
}