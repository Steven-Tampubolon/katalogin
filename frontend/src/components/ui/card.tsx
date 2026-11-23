import * as React from "react"
import { cn } from "@/lib/utils"

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string
}

export const CardContent = React.forwardRef<HTMLDivElement, CardProps>((props, ref) => {
  return (
    <div
      className={cn(
        "rounded-xl border border-background bg-card p-6",
        props.className,
      )}
      ref={ref}
    />
  )
})

CardContent.displayName = "Card"