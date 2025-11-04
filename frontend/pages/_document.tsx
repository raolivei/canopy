import Document, {
  DocumentContext,
  Html,
  Head,
  Main,
  NextScript
} from 'next/document';

class LedgerLightDocument extends Document {
  static async getInitialProps(ctx: DocumentContext) {
    const initialProps = await Document.getInitialProps(ctx);

    return { ...initialProps };
  }

  render() {
    return (
      <Html lang="en">
        <Head />
        <body className="bg-ledger-light text-slate-900 antialiased">
          <Main />
          <NextScript />
        </body>
      </Html>
    );
  }
}

export default LedgerLightDocument;

