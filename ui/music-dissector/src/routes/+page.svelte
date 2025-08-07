<script lang="ts">
  import { base } from '$app/paths'
  import tracks from '$lib/tracks'
  import { loading } from '$lib/stores'

  $loading = false
</script>

<svelte:head>
  <title>Music Dissector - Select a Track</title>
</svelte:head>

<div class="min-h-screen bg-surface-900 text-white">
  <div class="container mx-auto px-4 py-16">
    <h1 class="text-4xl font-bold text-center mb-12">Music Dissector</h1>
    
    <div class="max-w-2xl mx-auto">
      <h2 class="text-2xl font-semibold mb-6">Select a Track</h2>
      
      <div class="space-y-4">
        {#each tracks as track}
          <a 
            href="{base}/{encodeURIComponent(track)}"
            class="block p-6 bg-surface-800 hover:bg-surface-700 rounded-lg transition-colors duration-200"
          >
            <h3 class="text-xl font-medium">{track}</h3>
            <p class="text-surface-400 mt-2">Click to analyze this track</p>
          </a>
        {/each}
      </div>
      
      {#if tracks.length === 0}
        <div class="text-center py-12">
          <p class="text-surface-400">No tracks available</p>
          <p class="text-surface-500 mt-2">Please analyze some music files first</p>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
  }
</style>
