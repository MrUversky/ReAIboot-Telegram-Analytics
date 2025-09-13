import React from 'react'

interface JsonHighlighterProps {
  data: any
}

export const JsonHighlighter: React.FC<JsonHighlighterProps> = ({ data }) => {
  const highlightJson = (obj: any, indent = 0): React.JSX.Element => {
    const indentStr = '  '.repeat(indent)

    if (obj === null) {
      return <span className="text-blue-600">null</span>
    }

    if (typeof obj === 'boolean') {
      return <span className="text-purple-600">{obj.toString()}</span>
    }

    if (typeof obj === 'number') {
      return <span className="text-green-600">{obj}</span>
    }

    if (typeof obj === 'string') {
      return <span className="text-red-600">"{obj}"</span>
    }

    if (Array.isArray(obj)) {
      if (obj.length === 0) {
        return <span className="text-gray-600">[]</span>
      }

      return (
        <span>
          [<br />
          {obj.map((item, index) => (
            <span key={index}>
              {indentStr}  {highlightJson(item, indent + 1)}
              {index < obj.length - 1 ? ',' : ''}
              <br />
            </span>
          ))}
          {indentStr}]
        </span>
      )
    }

    if (typeof obj === 'object') {
      const keys = Object.keys(obj)
      if (keys.length === 0) {
        return <span className="text-gray-600">{'{}'}</span>
      }

      return (
        <span>
          {'{'}<br />
          {keys.map((key, index) => (
            <span key={key}>
              {indentStr}  <span className="text-blue-800">"{key}"</span>: {highlightJson(obj[key], indent + 1)}
              {index < keys.length - 1 ? ',' : ''}
              <br />
            </span>
          ))}
          {indentStr}{'}'}
        </span>
      )
    }

    return <span className="text-gray-600">{String(obj)}</span>
  }

  try {
    return (
      <div className="font-mono text-xs overflow-x-auto">
        {highlightJson(data)}
      </div>
    )
  } catch (error) {
    return (
      <div className="text-red-600 text-xs">
        Ошибка отображения JSON: {String(error)}
      </div>
    )
  }
}
