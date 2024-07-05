
import base64

# usage: 
# 1) download the font (.tff)
# 2) e.g. NotoSansSC-Light.ttf (if download from google font, it's in the static folder)
# 3) >> python ttf_to_base64.py "path/to/font.ttf" "path/to/font.ts"
# 4) font.ts is that file stores your base64 string (.ts means available for typescript import)
# 5) place the newly generated font.ts to $lib/component/data/, it can be any where actually, I prefer there
# 6) a font.tff(in base64) file usually are bigger than code, especially for Chinese font 
#    but you always have option to upload the base64 code to somewhere, and when use just fetch that for one time use
#    that way you don't have to include that within your application source code, reduce the size greatly

def ttf_to_base64(ttf_path, output_path):
    with open(ttf_path, "rb") as ttf_file:
        ttf_data = ttf_file.read()
        base64_data = base64.b64encode(ttf_data).decode("utf-8")

    with open(output_path, "w") as output_file:
        output_file.write(f'export const Base64Font: string = `\n{base64_data}\n`;')

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python ttf_to_base64.py <input.ttf> <output.ts>")
    else:
        ttf_to_base64(sys.argv[1], sys.argv[2])
