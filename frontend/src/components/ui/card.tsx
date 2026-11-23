import * as React from "react"
import { cn } from "@/lib/utils"

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>((props, ref) => {
  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-card p-6",
        props.className,
      )}
      ref={ref}
    />
  )
})

Card.displayName = "Card"