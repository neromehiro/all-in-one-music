import { error } from '@sveltejs/kit'
import { readFile } from 'fs/promises'
import { join } from 'path'
import { gunzipSync } from 'zlib'

export async function load({ params }) {
  const { track } = params
  
  try {
    // プロジェクトルートからの相対パス
    const dataPath = join(process.cwd(), '../../all-in-one/output_test', track, 'music-dissector/data')
    
    // まずgzip圧縮されたファイルを試す
    let data
    try {
      const gzPath = join(dataPath, `${track}.json.gz`)
      const gzBuffer = await readFile(gzPath)
      const decompressed = gunzipSync(gzBuffer)
      data = JSON.parse(decompressed.toString())
    } catch (e) {
      // gzipファイルが見つからない場合は通常のJSONを試す
      const jsonPath = join(dataPath, `${track}.json`)
      const jsonContent = await readFile(jsonPath, 'utf-8')
      data = JSON.parse(jsonContent)
    }
    
    // 音声ファイルのURLを追加
    return {
      ...data,
      audioUrls: {
        mixdown: `/api/audio/${track}/mixdown`,
        demixed: {
          bass: `/api/audio/${track}/bass`,
          drum: `/api/audio/${track}/drum`,
          other: `/api/audio/${track}/other`,
          vocal: `/api/audio/${track}/vocal`
        }
      }
    }
  } catch (err) {
    console.error('Error loading track data:', err)
    throw error(404, `Track not found: ${track}`)
  }
}
