import * as React from "react"
import { cn } from "@/lib/utils"

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>((props, ref) => {
  return (
    <div
      className={cn(
        "rounded-xl border border-background bg-card p-6",
        props.className,
      )}
      ref={ref}
    >
      {props.children}
    </div>
  )
})

Card.displayName = "Card"

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

CardContent.displayName = "CardContent"

export const CardHeader = React.forwardRef<HTMLDivElement, CardProps>((props, ref) => {
  return (
    <div
      className={cn(
        "pb-3 border-b border-background",
        props.className,
      )}
      ref={ref}
    >
      {props.children}
    </div>
  )
})

CardHeader.displayName = "CardHeader"