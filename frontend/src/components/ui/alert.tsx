import * as React from "react"
import { cn } from "@/lib/utils"

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string
}

export const Alert = React.forwardRef<HTMLDivElement, AlertProps>((props, ref) => {
  return (
    <div
      className={cn(
        "rounded-md border p-4 bg-destructive/10 text-destructive",
        props.className,
      )}
      ref={ref}
    />
  )
})

Alert.displayName = "Alert"