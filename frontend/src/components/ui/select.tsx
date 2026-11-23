import * as React from "react"
import { cn } from "@/lib/utils"

export interface SelectProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string
}

export const SelectTrigger = React.forwardRef<HTMLButtonElement, SelectProps>((props, ref) => {
  return (
    <button
      ref={ref}
      className={cn(
        "rounded-md bg-input h-11 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        props.className,
      )}
    />
  )
})

SelectTrigger.displayName = "SelectTrigger"

export const SelectContent = React.forwardRef<HTMLDivElement, SelectProps>((props, ref) => {
  return (
    <div
      ref={ref}
      className={cn(
        "absolute right-0 top-full mt-1 w-64 rounded-md bg-card py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:visible:outline-none",
        props.className,
      )}
    />
  )
})

SelectContent.displayName = "SelectContent"

export const Select = React.forwardRef<HTMLDivElement, SelectProps>((props, ref) => {
  return (
    <div
      className={cn(
        "relative",
        props.className,
      )}
      ref={ref}
    />
  )
})

Select.displayName = "Select"

export const SelectSeparator = React.forwardRef<HTMLDivElement, SelectProps>((_props, ref) => {
  return <div className="my-1" ref={ref} />
})

SelectSeparator.displayName = "SelectSeparator"

export const SelectValue = React.forwardRef<HTMLDivElement, SelectProps>((props, ref) => {
  return <div className="px-2 py-1" ref={ref}>{props.children}</div>
})

SelectValue.displayName = "SelectValue"