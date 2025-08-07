import { error } from '@sveltejs/kit'
import { createReadStream } from 'fs'
import { stat } from 'fs/promises'
import { join } from 'path'

export async function GET({ params }) {
  const { track, stem } = params
  
  try {
    let audioPath: string
    
    if (stem === 'mixdown') {
      // ミックスダウンファイル
      audioPath = join(
        process.cwd(),
        '../../all-in-one/output_test',
        track,
        'music-dissector/mixdown',
        `${track}.mp3`
      )
    } else {
      // ステムファイル
      audioPath = join(
        process.cwd(),
        '../../all-in-one/output_test',
        track,
        'music-dissector/demixed',
        track,
        `${stem}.mp3`
      )
    }
    
    // ファイルの存在確認
    const stats = await stat(audioPath)
    
    // ストリーミングレスポンスを返す
    return new Response(createReadStream(audioPath) as any, {
      headers: {
        'Content-Type': 'audio/mpeg',
        'Content-Length': stats.size.toString(),
        'Cache-Control': 'public, max-age=3600'
      }
    })
  } catch (err) {
    console.error('Error serving audio file:', err)
    throw error(404, 'Audio file not found')
  }
}
