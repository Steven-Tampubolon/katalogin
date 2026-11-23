import * as React from "react"
import { cn } from "@/lib/utils"

export interface BadgeProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link"
}

export const Badge = React.forwardRef<HTMLButtonElement, BadgeProps>((props, ref) => {
  const { variant = "default", className, ...propsRest } = props
  const variants = {
    default: "inline-flex items-center rounded-md bg-muted px-2.5 py-0.5 text-xs font-medium",
    destructive: "inline-flex items-center rounded-md bg-destructive text-destructive-foreground px-2.5 py-0.5 text-xs font-medium",
    outline: "inline-flex items-center rounded-md border border-border px-2.5 py-0.5 text-xs font-medium",
    secondary: "inline-flex items-center rounded-md bg-secondary text-secondary-foreground px-2.5 py-0.5 text-xs font-medium",
    ghost: "inline-flex items-center rounded-md bg-transparent px-2.5 py-0.5 text-xs font-medium",
    link: "underline-offset-4 hover:underline",
  }

  return (
    <button
      className={cn("inline-flex items-center rounded-md bg-muted px-2.5 py-0.5 text-xs font-medium", variants[variant], className)}
      {...propsRest}
      ref={ref}
    />
  )
})

Badge.displayName = "Badge"