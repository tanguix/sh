
<script lang="ts">
  export let message: string = "Loading...";
</script>

<div class="loading">
  <div class="bouncing-loader">
    <div></div>
    <div></div>
    <div></div>
  </div>
  <p>{message}</p>
</div>

<style>
  .loading {
    text-align: center;
    padding: 20px;
    font-size: 18px;
    color: #666;
  }

  .bouncing-loader {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 40px;
  }

  .bouncing-loader > div {
    width: 12px;
    height: 12px;
    margin: 0 4px;
    background: #7aa2f7;
    border-radius: 50%;
    animation: bouncing-loader 0.6s infinite alternate;
  }

  .bouncing-loader > div:nth-child(2) {
    animation-delay: 0.2s;
  }

  .bouncing-loader > div:nth-child(3) {
    animation-delay: 0.4s;
  }

  @keyframes bouncing-loader {
    to {
      transform: translateY(-10px);
    }
  }
</style>
