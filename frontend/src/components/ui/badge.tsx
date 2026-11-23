import * as React from "react"
import { cn } from "@/lib/utils"

export interface BadgeProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link"
}

export const badgeVariants = {
  default: "inline-flex items-center rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium",
  destructive: "inline-flex items-center rounded-full bg-destructive text-destructive-foreground px-2.5 py-0.5 text-xs font-medium",
  outline: "inline-flex items-center rounded-full border border-border px-2.5 py-0.5 text-xs font-medium",
  secondary: "inline-flex items-center rounded-full bg-secondary text-secondary-foreground px-2.5 py-0.5 text-xs font-medium",
  ghost: "inline-flex items-center rounded-full bg-transparent px-2.5 py-0.5 text-xs font-medium",
  link: "underline-offset-4 hover:underline",
}

export const Badge = React.forwardRef<HTMLButtonElement, BadgeProps>((props, ref) => {
  const { variant = "default", className, ...propsRest } = props
  return (
    <button
      className={cn("inline-flex items-center rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium", badgeVariants[variant], className)}
      {...propsRest}
      ref={ref}
    />
  )
})

Badge.displayName = "Badge"